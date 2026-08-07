#!/usr/bin/env python3
"""Create a digest manifest and minimal GCP bundle for CHARM GRPO r1."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INCLUDE = (
    Path("configs/charm_compiler_grpo/r1.json"),
    Path("configs/public_pr_eval/public-pr-repo-eval-v2-r5.jsonl"),
    Path("configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v2.jsonl"),
    Path("configs/public_pr_eval/private_probes"),
    Path("artifacts/charm-compiler-grpo/r1/data"),
    Path("artifacts/charm-compiler-grpo/r1/executable-oracle-receipt.json"),
    Path("docker/charm-compiler-grpo-gcp/Dockerfile"),
    Path("docker/charm-compiler-grpo-gcp/Verifier.Dockerfile"),
    Path("docker/public-pr-synthmem-gcp/Dockerfile"),
    Path("examples/grpo.sh"),
    Path("scripts/train_grpo.sh"),
    Path("scripts/check_runtime.py"),
    Path("scripts/prepare_grpo_adapter.py"),
    Path("scripts/reconstruct_megatron_lora.py"),
    Path("scripts/convert_checkpoint.sh"),
    Path("scripts/publish_results.py"),
    Path("scripts/run_charm_compiler_guided.py"),
    Path("scripts/public_pr_repo_eval.py"),
    Path("scripts/validate_public_pr_eval.py"),
    Path("scripts/gcp_public_pr_synthmem_50ep_eval.py"),
    Path("scripts/gcp_charm_grpo_pipeline.py"),
    Path("scripts/gcp_charm_grpo_pipeline.sh"),
    Path("src/glm47_posttraining/__init__.py"),
    Path("src/glm47_posttraining/constants.py"),
    Path("src/glm47_posttraining/aider_polyglot"),
    Path("src/glm47_posttraining/cpp_perf"),
    Path("src/glm47_posttraining/integrations"),
    Path("src/glm47_posttraining/public_pr_eval"),
)


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_entry(relative: Path, root: Path) -> None:
    source = REPO_ROOT / relative
    target = root / relative
    if source.is_symlink() or not source.exists():
        raise FileNotFoundError(f"bundle input is missing or a symlink: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        for item in source.rglob("*"):
            if item.is_symlink():
                raise ValueError(f"bundle input contains a symlink: {item}")
        shutil.copytree(
            source,
            target,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".DS_Store"),
        )
    else:
        shutil.copy2(source, target)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", default="/tmp/charm-compiler-grpo-gcp-r1.tgz", type=Path
    )
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"refusing to overwrite bundle: {output}")
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
    ).strip()
    with tempfile.TemporaryDirectory(prefix="charm-grpo-gcp-bundle-") as value:
        staging = Path(value)
        for relative in INCLUDE:
            copy_entry(relative, staging)
        (staging / "SOURCE_COMMIT").write_text(commit + "\n", encoding="utf-8")
        files = []
        for path in sorted(item for item in staging.rglob("*") if item.is_file()):
            files.append(
                {
                    "path": path.relative_to(staging).as_posix(),
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256_path(path),
                }
            )
        manifest = {
            "schema_version": "charm-compiler-grpo-gcp-bundle-v1",
            "decision": "PASS",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_commit": commit,
            "file_count": len(files),
            "files": files,
            "training_image_excludes_public_pr_eval": True,
            "heldout_files_are_for_separate_eval_image_only": True,
        }
        (staging / "BUNDLE-MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix(output.suffix + f".tmp-{os.getpid()}")
        with tarfile.open(temporary, "w:gz") as archive:
            for path in sorted(staging.iterdir()):
                archive.add(path, arcname=path.name, recursive=True)
        os.replace(temporary, output)
    print(f"BUNDLE={output}")
    print(f"BUNDLE_SHA256={sha256_path(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
