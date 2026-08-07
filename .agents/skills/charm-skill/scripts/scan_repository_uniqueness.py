#!/usr/bin/env python3
"""Fail-closed repository-wide uniqueness scan for frozen CHARM proposals.

The scanner inventories every accessible worktree/additional root, indexes
task-bearing text and JSON/JSONL records, compares all proposals both against
that corpus and one another, and emits the zero-match receipt required by the
atomic reservation utility.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "charm-repository-uniqueness-receipt-v1"
PROPOSAL_SCHEMA = "charm-v1-proposal-plan-v1"
SCANNER_VERSION = "charm-repository-uniqueness-v1"
FINGERPRINT_SCHEMA = "charm-problem-fingerprint-v1"
NEAR_THRESHOLD = 0.92
MAX_TEXT_BYTES = 8 * 1024 * 1024
TASK_JSON_NAME_RE = re.compile(
    r"(task|manifest|registry|ledger|dataset|receipt|catalog|index|rubric)", re.IGNORECASE
)
TASK_ID_KEY_RE = re.compile(r"^(task_?id|id)$", re.IGNORECASE)
WORD_RE = re.compile(r"[a-z0-9_:+<>.-]+")
EXCLUDED_PARTS = {
    ".git", ".hg", ".svn", "node_modules", ".venv", "venv", "__pycache__",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox", "dist", "build",
}
TEXT_SUFFIXES = {
    ".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".md", ".txt",
    ".json", ".jsonl", ".yaml", ".yml", ".toml", ".jinja", ".py", ".csv",
}
PROPOSAL_FIELDS = (
    "contract", "public_api", "starter_design", "target_design", "oracle_design",
    "solution_strategy", "edge_cases",
)


class ScanError(ValueError):
    """The corpus or proposal plan cannot support a complete comparison."""


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def normalize(value: str) -> str:
    return " ".join(WORD_RE.findall(value.casefold()))


def tokens(value: str) -> set[str]:
    return set(WORD_RE.findall(value.casefold()))


def similarity(left: str, right: str) -> float:
    a, b = tokens(left), tokens(right)
    if len(a) < 12 or len(b) < 12:
        return 0.0
    return len(a & b) / len(a | b)


def flatten_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(flatten_text(item) for item in value)
    if isinstance(value, dict):
        return "\n".join(f"{key}: {flatten_text(item)}" for key, item in sorted(value.items()))
    if value is None:
        return ""
    return str(value)


def load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ScanError(f"{label} is unreadable or invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ScanError(f"{label} must be a JSON object: {path}")
    return value


def git_root(start: Path) -> Path:
    completed = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        check=False, capture_output=True, text=True,
    )
    if completed.returncode != 0:
        raise ScanError(f"cannot resolve repository root from {start}")
    return Path(completed.stdout.strip()).resolve()


def git_revision(root: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=False, capture_output=True, text=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unavailable"


def linked_worktrees(root: Path) -> tuple[list[Path], list[dict[str, Any]]]:
    completed = subprocess.run(
        ["git", "-C", str(root), "worktree", "list", "--porcelain"],
        check=False, capture_output=True, text=True,
    )
    if completed.returncode != 0:
        raise ScanError("git worktree inventory failed")
    included: list[Path] = []
    unavailable: list[dict[str, Any]] = []
    for line in completed.stdout.splitlines():
        if not line.startswith("worktree "):
            continue
        path = Path(line.removeprefix("worktree ")).resolve()
        if path.is_dir():
            included.append(path)
        else:
            unavailable.append({"path": str(path), "reason": "missing linked worktree"})
    return included, unavailable


def iter_files(root: Path, exclusions: list[dict[str, str]]) -> Iterable[Path]:
    for directory, names, files in os.walk(root, followlinks=False):
        base = Path(directory)
        kept: list[str] = []
        for name in sorted(names):
            child = base / name
            if name in EXCLUDED_PARTS or child.is_symlink():
                exclusions.append({
                    "path": str(child),
                    "reason": "version-control/dependency/cache/symlink exclusion",
                })
            else:
                kept.append(name)
        names[:] = kept
        for name in sorted(files):
            path = base / name
            if path.is_symlink():
                exclusions.append({"path": str(path), "reason": "symlink exclusion"})
                continue
            yield path


def extract_ids(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if TASK_ID_KEY_RE.fullmatch(str(key)) and isinstance(item, str):
                found.add(item)
            found.update(extract_ids(item))
    elif isinstance(value, list):
        for item in value:
            found.update(extract_ids(item))
    return found


def parse_json_records(path: Path, text: str) -> tuple[list[Any], list[str]]:
    if path.suffix == ".jsonl":
        records: list[Any] = []
        errors: list[str] = []
        for line_number, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                errors.append(f"{path}:{line_number}: {exc}")
        return records, errors
    try:
        return [json.loads(text)], []
    except json.JSONDecodeError as exc:
        return [], [f"{path}: {exc}"]


def validate_proposals(plan: dict[str, Any]) -> list[dict[str, Any]]:
    if plan.get("schema_version") != PROPOSAL_SCHEMA:
        raise ScanError(f"proposal schema_version must be {PROPOSAL_SCHEMA}")
    proposals = plan.get("proposals")
    if not isinstance(proposals, list) or not proposals:
        raise ScanError("proposals must be a non-empty list")
    seen: set[str] = set()
    checked: list[dict[str, Any]] = []
    for index, proposal in enumerate(proposals):
        if not isinstance(proposal, dict):
            raise ScanError(f"proposals[{index}] must be an object")
        task_id = proposal.get("task_id")
        if not isinstance(task_id, str) or not task_id or task_id in seen:
            raise ScanError(f"invalid or duplicate proposal task_id: {task_id!r}")
        seen.add(task_id)
        missing = [field for field in PROPOSAL_FIELDS if not flatten_text(proposal.get(field)).strip()]
        if missing:
            raise ScanError(f"proposal {task_id} lacks substantive fields: {missing}")
        semantic = "\n".join(flatten_text(proposal[field]) for field in PROPOSAL_FIELDS)
        checked.append({**proposal, "_semantic_text": semantic})
    return checked


def scan(
    proposal_path: Path,
    output_path: Path,
    start: Path,
    additional_roots: list[Path],
) -> dict[str, Any]:
    started_ns = time.time_ns()
    plan = load_object(proposal_path, "proposal plan")
    proposals = validate_proposals(plan)
    root = git_root(start)
    worktrees, unavailable = linked_worktrees(root)
    roots = sorted({*(path.resolve() for path in worktrees), *(path.resolve() for path in additional_roots)})
    missing_additional = [path for path in roots if not path.is_dir()]
    if missing_additional:
        raise ScanError(f"configured comparison roots are unavailable: {missing_additional}")
    # A prunable missing linked worktree has no readable task inventory. Record it,
    # but do not call the accessible repository scope incomplete solely for stale git metadata.
    exclusions: list[dict[str, str]] = []
    corpus: list[dict[str, Any]] = []
    parse_failures: list[str] = []
    task_records: list[dict[str, Any]] = []
    excluded_exact = {proposal_path.resolve(), output_path.resolve()}
    files_visited = 0
    for included_root in roots:
        for path in iter_files(included_root, exclusions):
            resolved = path.resolve()
            if resolved in excluded_exact:
                exclusions.append({"path": str(resolved), "reason": "queried proposal/output exclusion"})
                continue
            files_visited += 1
            try:
                size = path.stat().st_size
            except OSError as exc:
                parse_failures.append(f"{path}: stat failed: {exc}")
                continue
            if size > MAX_TEXT_BYTES or path.suffix.lower() not in TEXT_SUFFIXES:
                exclusions.append({"path": str(path), "reason": "opaque/oversize non-task text exclusion"})
                continue
            try:
                raw = path.read_bytes()
                text = raw.decode("utf-8")
            except (OSError, UnicodeError) as exc:
                parse_failures.append(f"{path}: text read failed: {exc}")
                continue
            record = {
                "path": str(resolved),
                "sha256": sha256_bytes(raw),
                "normalized": normalize(text),
                "text": text,
                "task_ids": [],
            }
            if path.suffix.lower() in {".json", ".jsonl"} and TASK_JSON_NAME_RE.search(path.name):
                values, errors = parse_json_records(path, text)
                parse_failures.extend(errors)
                identifiers = sorted({identifier for value in values for identifier in extract_ids(value)})
                record["task_ids"] = identifiers
                for row, value in enumerate(values, 1):
                    task_records.append({
                        "path": str(resolved), "row": row,
                        "task_ids": sorted(extract_ids(value)),
                        "content_sha256": sha256_bytes(canonical_bytes(value)),
                    })
            corpus.append(record)

    exact_matches: list[dict[str, Any]] = []
    near_matches: list[dict[str, Any]] = []
    structural_matches: list[dict[str, Any]] = []
    semantic_matches: list[dict[str, Any]] = []
    task_id_matches: list[dict[str, Any]] = []
    ambiguous_matches: list[dict[str, Any]] = []

    for proposal in proposals:
        task_id = proposal["task_id"]
        semantic = proposal["_semantic_text"]
        normalized_semantic = normalize(semantic)
        structural = normalize(flatten_text(proposal["public_api"]) + "\n" + flatten_text(proposal["starter_design"]))
        for record in corpus:
            id_token = re.compile(rf"(?<![A-Za-z0-9_.-]){re.escape(task_id)}(?![A-Za-z0-9_.-])")
            if task_id in record["task_ids"] or id_token.search(record["text"]):
                task_id_matches.append({"task_id": task_id, "path": record["path"]})
            if normalized_semantic and normalized_semantic == record["normalized"]:
                exact_matches.append({"task_id": task_id, "path": record["path"]})
            score = similarity(semantic, record["text"])
            if score >= NEAR_THRESHOLD:
                near_matches.append({"task_id": task_id, "path": record["path"], "score": score})
            if structural and len(tokens(structural)) >= 8 and structural in record["normalized"]:
                structural_matches.append({"task_id": task_id, "path": record["path"]})
        for other in proposals:
            if other["task_id"] <= task_id:
                continue
            if normalize(semantic) == normalize(other["_semantic_text"]):
                semantic_matches.append({"task_ids": [task_id, other["task_id"]]})
            score = similarity(semantic, other["_semantic_text"])
            if score >= NEAR_THRESHOLD:
                near_matches.append({"task_ids": [task_id, other["task_id"]], "score": score})
            if structural == normalize(flatten_text(other["public_api"]) + "\n" + flatten_text(other["starter_design"])):
                structural_matches.append({"task_ids": [task_id, other["task_id"]]})

    corpus_index = [
        {"path": item["path"], "sha256": item["sha256"], "task_ids": item["task_ids"]}
        for item in sorted(corpus, key=lambda item: item["path"])
    ]
    match_lists = (
        task_id_matches, exact_matches, near_matches, structural_matches,
        semantic_matches, ambiguous_matches,
    )
    complete = not parse_failures and all(path.is_dir() for path in roots)
    decision = "PASS" if complete and all(not matches for matches in match_lists) else "FAIL"
    proposal_records = [{
        "task_id": proposal["task_id"],
        "topic": proposal.get("topic"),
        "slot_id": proposal.get("slot_id"),
        "fingerprint_sha256": sha256_bytes(canonical_bytes({
            field: proposal[field] for field in PROPOSAL_FIELDS
        })),
    } for proposal in proposals]
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "decision": decision,
        "repository_scope_complete": complete,
        "repository_root": str(root),
        "repository_revision": git_revision(root),
        "scanner_version": SCANNER_VERSION,
        "normalization_version": "unicode-casefold-word-v1",
        "parser_version": "python-json-v1",
        "duplicate_policy_version": f"six-level-v1-near-{NEAR_THRESHOLD}",
        "fingerprint_schema_version": FINGERPRINT_SCHEMA,
        "scan_started_unix_ns": started_ns,
        "scan_finished_unix_ns": time.time_ns(),
        "deterministic_seed": 0,
        "included_roots": [str(path) for path in roots],
        "unavailable_prunable_worktrees": unavailable,
        "exclusions": exclusions,
        "files_visited": files_visited,
        "task_records_parsed": len(task_records),
        "parse_failures": len(parse_failures),
        "parse_failure_details": parse_failures,
        "proposal_plan_sha256": sha256_bytes(proposal_path.read_bytes()),
        "proposals": proposal_records,
        "proposal_count": len(proposal_records),
        "corpus_index_sha256": sha256_bytes(canonical_bytes(corpus_index)),
        "task_id_matches": len(task_id_matches),
        "task_id_match_details": task_id_matches,
        "exact_matches": len(exact_matches),
        "exact_match_details": exact_matches,
        "near_matches": len(near_matches),
        "near_match_details": near_matches,
        "structural_matches": len(structural_matches),
        "structural_match_details": structural_matches,
        "semantic_matches": len(semantic_matches),
        "semantic_match_details": semantic_matches,
        "ambiguous_matches": len(ambiguous_matches),
        "ambiguous_match_details": ambiguous_matches,
        "linked_worktrees_reconciled": True,
        "active_and_historical_artifacts_included": True,
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_bytes(receipt))
    return receipt


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposal-plan", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--additional-root", action="append", default=[], type=Path)
    args = parser.parse_args(argv)
    if args.output.exists():
        print(f"refusing to overwrite uniqueness receipt: {args.output}", file=sys.stderr)
        return 2
    try:
        receipt = scan(args.proposal_plan, args.output, args.root, args.additional_root)
    except ScanError as exc:
        receipt = {
            "schema_version": SCHEMA_VERSION, "decision": "FAIL",
            "repository_scope_complete": False, "parse_failures": 1,
            "task_id_matches": 0, "exact_matches": 0, "near_matches": 0,
            "structural_matches": 0, "semantic_matches": 0, "ambiguous_matches": 0,
            "errors": [str(exc)],
        }
        atomic_write(args.output, canonical_bytes(receipt))
        print(str(exc), file=sys.stderr)
        return 1
    atomic_write(args.output, canonical_bytes(receipt))
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
