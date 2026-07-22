#!/usr/bin/env python3
"""Publish one verified RL8 run to private, manually gated Hugging Face repos."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Any

from huggingface_hub import HfApi, hf_hub_download


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_regular(path: Path) -> None:
    if path.is_symlink() or not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"missing nonempty regular publication input: {path}")


def _add_file(files: dict[str, Path], remote_path: str, source: Path) -> None:
    _require_regular(source)
    if remote_path in files:
        raise RuntimeError(f"duplicate remote publication path: {remote_path}")
    files[remote_path] = source


def _selected_dataset_files(run_root: Path, preservation_root: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for path in sorted((run_root / "rollout_dumps").glob("grpo*.pt")):
        _add_file(files, f"rollout_dumps/{path.name}", path)
    for relative in (
        "input_receipt.json",
        "runtime_receipt.json",
        "task_split.json",
        "data/manifest.json",
        "data/grpo/train.jsonl",
        "data/eval/train_monitor.jsonl",
        "grpo_lora_r16/grpo_training_gate.json",
        "grpo_lora_r16/run_receipt.txt",
        "grpo_lora_r16/run.log",
        "grpo_lora_r16/vram_usage.csv",
        "grpo_lora_r16/vram_peak.txt",
    ):
        _add_file(files, relative, run_root / relative)
    for path in sorted((run_root / "signal_gates").glob("signal_gate_passed_*.json")):
        _add_file(files, f"signal_gates/{path.name}", path)
    for root_name in ("wandb", "sync_metrics"):
        root = run_root / root_name
        for path in sorted(root.rglob("*")):
            if path.is_file() and not path.is_symlink():
                _add_file(files, f"{root_name}/{path.relative_to(root).as_posix()}", path)
    for name in ("preservation_manifest.json", "SHA256SUMS"):
        _add_file(files, f"preservation/{name}", preservation_root / name)
    return files


def _selected_model_files(run_root: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    checkpoint_root = run_root / "checkpoints" / "grpo_lora_r16"
    slots = sorted(path for path in checkpoint_root.glob("iter_*") if path.is_dir())
    if len(slots) != 2:
        raise RuntimeError(f"RL8 publication requires two checkpoints, found {len(slots)}")
    for slot in slots:
        for path in sorted(slot.rglob("*")):
            if path.is_file() and not path.is_symlink():
                relative = path.relative_to(checkpoint_root).as_posix()
                _add_file(files, f"checkpoints/{relative}", path)
    reconstruction = run_root / "inputs" / "sft-v3-r16-ep8" / "native_reconstruction_manifest.json"
    _add_file(files, "inputs/native_reconstruction_manifest.json", reconstruction)
    _add_file(files, "inputs/input_receipt.json", run_root / "input_receipt.json")
    _add_file(files, "inputs/runtime_receipt.json", run_root / "runtime_receipt.json")
    return files


def _ensure_repo(api: HfApi, repo_id: str, repo_type: str) -> None:
    api.create_repo(repo_id=repo_id, repo_type=repo_type, private=True, exist_ok=True)
    api.update_repo_settings(repo_id=repo_id, repo_type=repo_type, private=True, gated="manual")
    info = api.repo_info(repo_id=repo_id, repo_type=repo_type)
    if info.private is not True or info.gated != "manual":
        raise RuntimeError(
            f"access gate failed for {repo_type} {repo_id}: "
            f"private={info.private!r} gated={info.gated!r}"
        )


def _manifest(files: dict[str, Path]) -> dict[str, dict[str, Any]]:
    return {
        remote: {
            "size_bytes": source.stat().st_size,
            "sha256": sha256_path(source),
        }
        for remote, source in sorted(files.items())
    }


def _stage(files: dict[str, Path], root: Path, manifest: dict[str, Any]) -> None:
    root.mkdir(parents=True)
    for remote, source in files.items():
        destination = root / remote
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(source, destination)
        except OSError:
            shutil.copy2(source, destination)
    (root / "UPLOAD_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _roundtrip(
    *,
    repo_id: str,
    repo_type: str,
    revision: str,
    token: str,
    base: str,
    records: dict[str, dict[str, Any]],
    verify_root: Path,
) -> None:
    for remote, record in sorted(records.items()):
        remote_path = f"{base}/{remote}"
        downloaded = Path(
            hf_hub_download(
                repo_id=repo_id,
                repo_type=repo_type,
                filename=remote_path,
                revision=revision,
                token=token,
                local_dir=verify_root / repo_type,
                force_download=True,
            )
        )
        if (
            downloaded.stat().st_size != record["size_bytes"]
            or sha256_path(downloaded) != record["sha256"]
        ):
            raise RuntimeError(f"remote round-trip mismatch: {repo_id}/{remote_path}")


def _upload_success(
    api: HfApi,
    *,
    repo_id: str,
    repo_type: str,
    token: str,
    path_in_repo: str,
    payload: dict[str, Any],
    verify_root: Path,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="rl8-success-") as temporary:
        path = Path(temporary) / "_SUCCESS.json"
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        commit = api.upload_file(
            path_or_fileobj=str(path),
            path_in_repo=path_in_repo,
            repo_id=repo_id,
            repo_type=repo_type,
            commit_message=f"Complete {payload['run_id']}",
        )
        downloaded = Path(
            hf_hub_download(
                repo_id=repo_id,
                repo_type=repo_type,
                filename=path_in_repo,
                revision=str(commit.oid),
                token=token,
                local_dir=verify_root / f"{repo_type}-success",
                force_download=True,
            )
        )
        if downloaded.read_bytes() != path.read_bytes():
            raise RuntimeError(f"remote success marker mismatch: {repo_id}/{path_in_repo}")
        return {"commit": str(commit.oid), "sha256": sha256_path(path)}


def publish(args: argparse.Namespace) -> dict[str, Any]:
    run_root = args.run_root.resolve()
    preservation_root = args.preservation_root.resolve()
    token_path = args.token_file.resolve()
    if stat.S_IMODE(token_path.stat().st_mode) != 0o600:
        raise RuntimeError("Hugging Face token file must have mode 0600")
    token = token_path.read_text(encoding="utf-8").strip()
    if not token:
        raise RuntimeError("Hugging Face token file is empty")
    preservation = json.loads(
        (preservation_root / "preservation_manifest.json").read_text(encoding="utf-8")
    )
    if preservation.get("status") != "passed" or preservation.get("run_id") != run_root.name:
        raise RuntimeError("local preservation gate is not passed or run-bound")

    api = HfApi(token=token)
    _ensure_repo(api, args.dataset_repo, "dataset")
    _ensure_repo(api, args.model_repo, "model")
    dataset_files = _selected_dataset_files(run_root, preservation_root)
    model_files = _selected_model_files(run_root)
    if len(list((run_root / "signal_gates").glob("signal_gate_passed_*.json"))) != 2:
        raise RuntimeError("remote publication requires exactly two passed signal gates")
    dataset_records = _manifest(dataset_files)
    model_records = _manifest(model_files)
    run_id = run_root.name
    base = f"runs/{run_id}"

    with tempfile.TemporaryDirectory(prefix=f"{run_id}-publish-") as temporary:
        staging = Path(temporary)
        dataset_manifest = {
            "schema_version": 1,
            "kind": "glm47-aider-rl8-dataset-upload-manifest",
            "status": "ready",
            "run_id": run_id,
            "files": dataset_records,
        }
        model_manifest = {
            "schema_version": 1,
            "kind": "glm47-aider-rl8-model-upload-manifest",
            "status": "ready",
            "run_id": run_id,
            "files": model_records,
        }
        dataset_stage = staging / "dataset"
        model_stage = staging / "model"
        _stage(dataset_files, dataset_stage, dataset_manifest)
        _stage(model_files, model_stage, model_manifest)
        dataset_commit = api.upload_folder(
            folder_path=str(dataset_stage),
            path_in_repo=base,
            repo_id=args.dataset_repo,
            repo_type="dataset",
            commit_message=f"Preserve RL8 data for {run_id}",
        )
        model_commit = api.upload_folder(
            folder_path=str(model_stage),
            path_in_repo=base,
            repo_id=args.model_repo,
            repo_type="model",
            commit_message=f"Preserve RL8 checkpoints for {run_id}",
        )
        dataset_records_with_manifest = {
            **dataset_records,
            "UPLOAD_MANIFEST.json": {
                "size_bytes": (dataset_stage / "UPLOAD_MANIFEST.json").stat().st_size,
                "sha256": sha256_path(dataset_stage / "UPLOAD_MANIFEST.json"),
            },
        }
        model_records_with_manifest = {
            **model_records,
            "UPLOAD_MANIFEST.json": {
                "size_bytes": (model_stage / "UPLOAD_MANIFEST.json").stat().st_size,
                "sha256": sha256_path(model_stage / "UPLOAD_MANIFEST.json"),
            },
        }
        verify_root = Path(args.verify_root).resolve() / run_id
        _roundtrip(
            repo_id=args.dataset_repo,
            repo_type="dataset",
            revision=str(dataset_commit.oid),
            token=token,
            base=base,
            records=dataset_records_with_manifest,
            verify_root=verify_root,
        )
        _roundtrip(
            repo_id=args.model_repo,
            repo_type="model",
            revision=str(model_commit.oid),
            token=token,
            base=base,
            records=model_records_with_manifest,
            verify_root=verify_root,
        )

    model_success = _upload_success(
        api,
        repo_id=args.model_repo,
        repo_type="model",
        token=token,
        path_in_repo=f"{base}/_SUCCESS.json",
        payload={
            "schema_version": 1,
            "kind": "glm47-aider-rl8-model-success",
            "status": "passed",
            "run_id": run_id,
            "files": len(model_records_with_manifest),
            "content_commit": str(model_commit.oid),
        },
        verify_root=Path(args.verify_root),
    )
    dataset_success = _upload_success(
        api,
        repo_id=args.dataset_repo,
        repo_type="dataset",
        token=token,
        path_in_repo=f"{base}/_SUCCESS.json",
        payload={
            "schema_version": 1,
            "kind": "glm47-aider-rl8-dataset-success",
            "status": "passed",
            "run_id": run_id,
            "files": len(dataset_records_with_manifest),
            "content_commit": str(dataset_commit.oid),
            "model_repo": args.model_repo,
            "model_success": model_success,
        },
        verify_root=Path(args.verify_root),
    )
    result = {
        "schema_version": 1,
        "kind": "glm47-aider-rl8-remote-publication-receipt",
        "status": "passed",
        "run_id": run_id,
        "dataset_repo": args.dataset_repo,
        "dataset_private": True,
        "dataset_gated": "manual",
        "dataset_success": dataset_success,
        "model_repo": args.model_repo,
        "model_private": True,
        "model_gated": "manual",
        "model_success": model_success,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_root", type=Path)
    parser.add_argument("preservation_root", type=Path)
    parser.add_argument("--token-file", type=Path, required=True)
    parser.add_argument("--dataset-repo", required=True)
    parser.add_argument("--model-repo", required=True)
    parser.add_argument("--verify-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(publish(args), indent=2, sort_keys=True))


if __name__ == "__main__":
    os.umask(0o077)
    main()
