#!/usr/bin/env python3
"""Task-aware complete-corpus uniqueness scanner for CHARM V1.

Every accessible file is visited and classified.  Only genuine task-bearing
artifacts enter the problem-comparison index; generator/validator source is
retained in the scan ledger but cannot self-match the proposal it defines.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from decimal import Decimal, ROUND_CEILING
from pathlib import Path
from typing import Any, Iterable


STDLIB_RE = re

SCHEMA = "charm-repository-uniqueness-receipt-v5"
PROPOSAL_SCHEMA = "charm-v1-proposal-plan-v1"
NEAR_THRESHOLD = 0.92
MAX_BYTES = 8 * 1024 * 1024
WORD_RE = re.compile(r"[a-z0-9_:+<>.-]+")
CPP_TOKEN_RE = re.compile(
    r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|'
    r"[A-Za-z_][A-Za-z0-9_]*|0[xX][0-9A-Fa-f]+|\d+(?:\.\d+)?|"
    r"==|!=|<=|>=|&&|\|\||\+\+|--|->|::|[{}()\[\];,:?~+*/%&|^!<>=.-]"
)
TASK_KEY_RE = re.compile(r"^(task_?id|exercise|testcase)$", re.IGNORECASE)
TASK_NAME_RE = re.compile(
    r"(task|manifest|registry|ledger|dataset|rubric|receipt|catalog|index|proposal|plan|pre)",
    re.I,
)
TEXT_SUFFIXES = {".c", ".cc", ".cpp", ".h", ".hpp", ".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".toml", ".csv", ".py", ".jinja"}
EXCLUDED_DIRS = {".git", ".hg", ".svn", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox"}
TASK_ROOT_MARKERS = {"tasks", "exercises", "practice", "aider-tasks", "fixed26", "benchmark", "benchmarks"}
NON_TASK_SOURCE_MARKERS = {"scripts", "src", "tests", ".agents", ".codex"}
PROPOSAL_FIELDS = ("contract", "public_api", "starter_design", "target_design", "oracle_design", "solution_strategy", "edge_cases")
CPP_KEYWORDS = {
    "alignas", "alignof", "auto", "bool", "break", "case", "catch", "char",
    "class", "const", "constexpr", "continue", "default", "delete", "do",
    "double", "else", "enum", "explicit", "false", "float", "for", "friend",
    "if", "inline", "int", "long", "namespace", "new", "noexcept", "nullptr",
    "operator", "private", "protected", "public", "return", "short", "signed",
    "sizeof", "static", "struct", "switch", "template", "this", "throw", "true",
    "try", "typedef", "typename", "union", "unsigned", "using", "virtual", "void",
    "volatile", "while", "std", "string", "vector", "array", "map", "set",
    "optional", "unique_ptr", "size_t", "uint32_t", "uint64_t", "int64_t",
}
CFG_TOKENS = {"if", "else", "for", "while", "do", "switch", "case", "catch", "throw", "return", "break", "continue", "&&", "||", "?"}


class ScanError(ValueError):
    pass


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@functools.lru_cache(maxsize=1024)
def norm(value: str) -> str:
    return " ".join(WORD_RE.findall(value.casefold()))


@functools.lru_cache(maxsize=1024)
def token_set(value: str) -> frozenset[str]:
    return frozenset(WORD_RE.findall(value.casefold()))


def similarity(left: str, right: str) -> float:
    a, b = token_set(left), token_set(right)
    if len(a) < 12 or len(b) < 12:
        return 0.0
    return len(a & b) / len(a | b)


def sequence_similarity(left: str, right: str, width: int = 4) -> float:
    a_tokens, b_tokens = left.split(), right.split()
    if len(a_tokens) < width or len(b_tokens) < width:
        return 1.0 if a_tokens == b_tokens and a_tokens else 0.0
    a = {tuple(a_tokens[i:i + width]) for i in range(len(a_tokens) - width + 1)}
    b = {tuple(b_tokens[i:i + width]) for i in range(len(b_tokens) - width + 1)}
    return len(a & b) / len(a | b)


def jaccard_features(value: str, *, sequence: bool) -> frozenset[object]:
    """Return the exact feature set consumed by a component similarity lane."""
    if not sequence:
        return frozenset(token_set(value))
    tokens = value.split()
    if len(tokens) < 4:
        return frozenset()
    return frozenset(
        tuple(tokens[index:index + 4]) for index in range(len(tokens) - 3)
    )


def overlap_probe_count(feature_count: int, threshold: float) -> int:
    """Return a rare-feature probe count that cannot drop a Jaccard match."""
    if feature_count <= 0:
        return 0
    required_overlap = int(
        (Decimal(str(threshold)) * feature_count).to_integral_value(
            rounding=ROUND_CEILING
        )
    )
    return max(1, feature_count - required_overlap + 1)


def flatten(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(flatten(item) for item in value)
    if isinstance(value, dict):
        return "\n".join(f"{key}: {flatten(item)}" for key, item in sorted(value.items()))
    return "" if value is None else str(value)


@functools.lru_cache(maxsize=1024)
def cpp_shape(value: str) -> str:
    """Identifier/literal-normalized C++ token shape used as an AST proxy."""
    tokens: list[str] = []
    for token in CPP_TOKEN_RE.findall(value):
        if token.startswith(('"', "'")):
            tokens.append("STR")
        elif re.fullmatch(r"0[xX][0-9A-Fa-f]+|\d+(?:\.\d+)?", token):
            tokens.append("NUM")
        elif re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token):
            tokens.append(token if token in CPP_KEYWORDS else "ID")
        else:
            tokens.append(token)
    return " ".join(tokens)


@functools.lru_cache(maxsize=1024)
def cfg_shape(value: str) -> str:
    """Control-flow/operator topology independent of user identifiers."""
    depth = 0
    result: list[str] = []
    for token in CPP_TOKEN_RE.findall(value):
        if token == "{":
            depth += 1
            result.append(f"OPEN{min(depth, 9)}")
        elif token == "}":
            result.append(f"CLOSE{min(depth, 9)}")
            depth = max(0, depth - 1)
        elif token in CFG_TOKENS:
            result.append(token)
    return " ".join(result)


@functools.lru_cache(maxsize=1024)
def api_graph(value: str) -> str:
    """Normalize namespaces/parameter identifiers while retaining API topology."""
    shaped = cpp_shape(value)
    return " ".join(token for token in shaped.split() if token not in {"OPEN1", "CLOSE1"})


@functools.lru_cache(maxsize=1024)
def test_oracle_shape(value: str) -> str:
    assertions = re.findall(r"assert\s*\((.*?)\)\s*;", value, flags=re.DOTALL)
    return " | ".join(cpp_shape(item) + " :: " + cfg_shape(item) for item in assertions)


def explode_task_values(value: Any) -> list[Any]:
    if isinstance(value, dict):
        for key in ("proposals", "tasks"):
            rows = value.get(key)
            if isinstance(rows, list) and rows and all(isinstance(row, dict) for row in rows):
                return rows
    return [value]


def component_projection(kind: str, value: str) -> str:
    if kind in {"public_api", "api_graph"}:
        return api_graph(value)
    if kind in {"target_source", "target_combined", "ast_shape"}:
        return cpp_shape(value)
    if kind == "cfg_shape":
        return cfg_shape(value)
    if kind in {"hidden_test", "test_oracle"}:
        return test_oracle_shape(value)
    return norm(value)


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ScanError(f"invalid proposal JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ScanError("proposal plan must be a JSON object")
    return value


def repository_root(start: Path) -> Path:
    run = subprocess.run(["git", "-C", str(start), "rev-parse", "--show-toplevel"], check=False, capture_output=True, text=True)
    if run.returncode:
        raise ScanError(f"cannot resolve repository root: {start}")
    return Path(run.stdout.strip()).resolve()


def revision(root: Path) -> str:
    run = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=False, capture_output=True, text=True)
    return run.stdout.strip() if run.returncode == 0 else "unavailable"


def worktrees(root: Path) -> tuple[list[Path], list[dict[str, str]]]:
    run = subprocess.run(["git", "-C", str(root), "worktree", "list", "--porcelain"], check=False, capture_output=True, text=True)
    if run.returncode:
        raise ScanError("cannot inventory linked worktrees")
    available, stale = [], []
    for line in run.stdout.splitlines():
        if line.startswith("worktree "):
            path = Path(line[9:]).resolve()
            if path.is_dir():
                available.append(path)
            else:
                stale.append({"path": str(path), "reason": "missing/prunable git worktree metadata"})
    return available, stale


def walk(root: Path, exclusions: list[dict[str, str]]) -> Iterable[Path]:
    for directory, names, files in os.walk(root, followlinks=False):
        base = Path(directory)
        retained = []
        for name in sorted(names):
            path = base / name
            if name in EXCLUDED_DIRS or path.is_symlink():
                exclusions.append({"path": str(path), "reason": "VCS/dependency/cache/symlink"})
            else:
                retained.append(name)
        names[:] = retained
        for name in sorted(files):
            path = base / name
            if path.is_symlink():
                exclusions.append({"path": str(path), "reason": "symlink"})
            else:
                yield path


def task_ids(value: Any) -> set[str]:
    result: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if TASK_KEY_RE.fullmatch(str(key)) and isinstance(item, str):
                result.add(item)
            result.update(task_ids(item))
    elif isinstance(value, list):
        for item in value:
            result.update(task_ids(item))
    return result


def is_task_root_text(path: Path) -> bool:
    lowered = {part.casefold() for part in path.parts}
    if lowered & TASK_ROOT_MARKERS:
        # Source/test directories named tests are not benchmark fixtures unless
        # a stronger task-root marker also exists.
        return True
    return False


def parse_structured(path: Path, text: str) -> tuple[list[Any], list[str]]:
    if path.suffix.lower() == ".jsonl":
        values, errors = [], []
        for line_number, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                values.append(json.loads(line))
            except json.JSONDecodeError as exc:
                errors.append(f"{path}:{line_number}: {exc}")
        return values, errors
    try:
        return [json.loads(text)], []
    except json.JSONDecodeError as exc:
        return [], [f"{path}: {exc}"]


def validate_plan(plan: dict[str, Any]) -> list[dict[str, Any]]:
    if plan.get("schema_version") != PROPOSAL_SCHEMA:
        raise ScanError(f"proposal schema must be {PROPOSAL_SCHEMA}")
    proposals = plan.get("proposals")
    protocol_id = plan.get("protocol_id", "task-generation-v1")
    if not isinstance(proposals, list):
        raise ScanError("proposal plan must contain a proposals list")
    if protocol_id == "task-generation-v1" and len(proposals) != 51:
        raise ScanError("V1 proposal plan must contain exactly 51 tasks")
    if protocol_id != "task-generation-v1":
        authorized_task_count = plan.get("authorized_task_count")
        if (
            isinstance(authorized_task_count, bool)
            or not isinstance(authorized_task_count, int)
            or authorized_task_count <= 0
            or authorized_task_count != len(proposals)
        ):
            raise ScanError(
                "non-V1 proposal plan authorized_task_count must be a positive "
                "integer equal to the proposal count"
            )
    ids: set[str] = set()
    result = []
    for item in proposals:
        if not isinstance(item, dict) or not isinstance(item.get("task_id"), str):
            raise ScanError("each proposal requires a task_id")
        if item["task_id"] in ids:
            raise ScanError(f"duplicate proposed task ID: {item['task_id']}")
        ids.add(item["task_id"])
        if any(not flatten(item.get(field)).strip() for field in PROPOSAL_FIELDS):
            raise ScanError(f"incomplete substantive proposal: {item['task_id']}")
        result.append(item)
    return result


def scan(
    plan_path: Path,
    output_path: Path,
    start: Path,
    additional: list[Path],
    query_artifacts: list[Path],
    generated_queries: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    started = time.time_ns()
    plan = load_object(plan_path)
    proposals = validate_plan(plan)
    root = repository_root(start)
    linked, stale = worktrees(root)
    roots = sorted({*(path.resolve() for path in linked), *(path.resolve() for path in additional)})
    missing = [str(path) for path in roots if not path.is_dir()]
    if missing:
        raise ScanError(f"configured task roots unavailable: {missing}")
    query = {plan_path.resolve(), output_path.resolve(), *(path.resolve() for path in query_artifacts)}
    exclusions: list[dict[str, str]] = []
    parse_errors: list[str] = []
    inventory: list[dict[str, Any]] = []
    task_corpus: list[dict[str, Any]] = []
    files_visited = 0
    classified_non_task = 0
    for included in roots:
        for path in walk(included, exclusions):
            files_visited += 1
            resolved = path.resolve()
            if resolved in query:
                exclusions.append({"path": str(resolved), "reason": "exact frozen proposal-suite query artifact"})
                continue
            try:
                size = path.stat().st_size
            except OSError as exc:
                parse_errors.append(f"{path}: stat: {exc}")
                continue
            suffix = path.suffix.lower()
            # Task-bearing JSONL is never an opaque payload.  The 8 MiB limit
            # protects unrelated logs/checkpoints, but skipping a dataset
            # projection would make the repository-wide uniqueness claim
            # false.  Parse every JSONL physical row regardless of file size.
            if (size > MAX_BYTES and suffix != ".jsonl") or suffix not in TEXT_SUFFIXES:
                exclusions.append({"path": str(resolved), "reason": "opaque/oversize non-task payload"})
                continue
            try:
                raw = path.read_bytes()
                text = raw.decode("utf-8")
            except (OSError, UnicodeError) as exc:
                parse_errors.append(f"{path}: UTF-8 read: {exc}")
                continue
            item = {"path": str(resolved), "sha256": digest(raw), "size": size}
            inventory.append(item)
            structured_values: list[Any] = []
            discovered_ids: set[str] = set()
            structured_candidate = path.suffix.lower() in {".json", ".jsonl"} and (
                path.suffix.lower() == ".jsonl" or TASK_NAME_RE.search(path.name) is not None
            )
            if structured_candidate:
                values, errors = parse_structured(path, text)
                # Invalid structured files are blocking only when their path is
                # task-bearing; unrelated fixtures/source examples remain classified.
                if errors and is_task_root_text(path):
                    parse_errors.extend(errors)
                structured_values = values
                for value in values:
                    discovered_ids.update(task_ids(value))
            owner_task_source = (
                path.suffix.lower() == ".py"
                and ("build_specs(" in text or ("SPECS" in text and "oracle_design" in text))
            )
            task_bearing = is_task_root_text(path) or bool(discovered_ids) or path.suffix.lower() == ".jsonl" or owner_task_source
            # Generator/validator source does not become a task merely because
            # it contains an example ID; structured registries still do.
            if not task_bearing:
                classified_non_task += 1
                continue
            if structured_values:
                row = 0
                for value in structured_values:
                    for task_value in explode_task_values(value):
                        row += 1
                        row_text = flatten(task_value)
                        task_corpus.append({
                            "path": str(resolved), "row": row, "text": row_text,
                            "normalized": norm(row_text), "task_ids": sorted(task_ids(task_value)),
                            "sha256": digest(canonical(task_value)),
                        })
            else:
                task_corpus.append({
                    "path": str(resolved), "row": None, "text": text,
                    "normalized": norm(text), "task_ids": sorted(discovered_ids),
                    "sha256": digest(raw),
                })

    matches: dict[str, list[dict[str, Any]]] = {
        "task_id": [], "exact": [], "near": [], "structural": [], "semantic": [], "ambiguous": []
    }
    ambiguity_threshold = max(0.80, NEAR_THRESHOLD - 0.07)
    comparison_threshold = min(NEAR_THRESHOLD, ambiguity_threshold)
    prepared: list[dict[str, Any]] = []
    indexed_tokens = {str(proposal["task_id"]) for proposal in proposals}
    for proposal in proposals:
        semantic = "\n".join(flatten(proposal[field]) for field in PROPOSAL_FIELDS)
        normalized = norm(semantic)
        semantic_tokens = token_set(normalized)
        rare_tokens: tuple[str, ...] = ()
        if comparison_threshold <= 1.0 and semantic_tokens:
            rare_count = min(
                len(semantic_tokens),
                max(1, int((1.0 - comparison_threshold) * len(semantic_tokens)) + 1),
            )
            # Any record at or above the threshold must contain at least one
            # member of every subset this large.  Long tokens are selected only
            # to reduce false-positive candidates; the bound is exact.
            rare_tokens = tuple(
                sorted(semantic_tokens, key=lambda token: (-len(token), token))[:rare_count]
            )
            indexed_tokens.update(rare_tokens)
        prepared.append({
            "proposal": proposal,
            "semantic": semantic,
            "normalized": normalized,
            "api": api_graph(flatten(proposal["public_api"])),
            "rare_tokens": rare_tokens,
        })

    token_postings: dict[str, set[int]] = {token: set() for token in indexed_tokens}
    normalized_postings: dict[str, list[int]] = {}
    api_size_postings: dict[int, list[int]] = {}
    indexed_pattern = None
    if indexed_tokens:
        alternatives = "|".join(
            STDLIB_RE.escape(token)
            for token in sorted(indexed_tokens, key=lambda token: (-len(token), token))
        )
        indexed_pattern = STDLIB_RE.compile(r"(?:^| )(" + alternatives + r")(?= |$)")
    proposed_ids = {str(proposal["task_id"]) for proposal in proposals}
    for record_index, record in enumerate(task_corpus):
        normalized_postings.setdefault(record["normalized"], []).append(record_index)
        if indexed_pattern is not None:
            for match in indexed_pattern.finditer(record["normalized"]):
                token_postings[match.group(1)].add(record_index)
        for discovered_id in record["task_ids"]:
            if discovered_id in proposed_ids:
                token_postings[discovered_id].add(record_index)
        if NEAR_THRESHOLD <= 1.0:
            token_count = sum(1 for _ in CPP_TOKEN_RE.finditer(record["text"]))
            api_size_postings.setdefault(token_count, []).append(record_index)

    for proposal_index, item in enumerate(prepared):
        proposal = item["proposal"]
        pid = str(proposal["task_id"])
        semantic = item["semantic"]
        normalized = item["normalized"]
        api = item["api"]
        for record_index in sorted(token_postings.get(pid, set())):
            record = task_corpus[record_index]
            matches["task_id"].append({"task_id": pid, "path": record["path"], "row": record["row"]})
        if normalized:
            for record_index in normalized_postings.get(normalized, []):
                record = task_corpus[record_index]
                matches["exact"].append({"task_id": pid, "path": record["path"], "row": record["row"]})
        candidate_indices: set[int] = set()
        for token in item["rare_tokens"]:
            candidate_indices.update(token_postings.get(token, set()))
        for record_index in sorted(candidate_indices):
            record = task_corpus[record_index]
            score = similarity(semantic, record["text"])
            if score >= NEAR_THRESHOLD:
                matches["near"].append({"task_id": pid, "path": record["path"], "row": record["row"], "score": score})
            elif score >= ambiguity_threshold:
                matches["ambiguous"].append({"task_id": pid, "path": record["path"], "row": record["row"], "score": score, "fingerprint": "semantic-contract"})
        if NEAR_THRESHOLD <= 1.0 and len(api.split()) >= 8:
            for record_index in api_size_postings.get(len(api.split()), []):
                record = task_corpus[record_index]
                if api == api_graph(record["text"]):
                    matches["structural"].append({"task_id": pid, "path": record["path"], "row": record["row"]})
        for other in proposals[proposal_index + 1:]:
            other_semantic = "\n".join(flatten(other[field]) for field in PROPOSAL_FIELDS)
            other_api = api_graph(flatten(other["public_api"]))
            if normalized == norm(other_semantic):
                matches["semantic"].append({"task_ids": [pid, other["task_id"]]})
            score = similarity(semantic, other_semantic)
            if score >= NEAR_THRESHOLD:
                matches["near"].append({"task_ids": [pid, other["task_id"]], "score": score})
            elif score >= ambiguity_threshold:
                matches["ambiguous"].append({"task_ids": [pid, other["task_id"]], "score": score, "fingerprint": "semantic-contract"})
            if NEAR_THRESHOLD <= 1.0 and api == other_api:
                matches["structural"].append({"task_ids": [pid, other["task_id"]]})

    sequence_kinds = {"api_graph", "ast_shape", "cfg_shape", "test_oracle"}
    indexed_component_kinds = sequence_kinds | {
        "oracle_behavior", "mutation_family", "semantic_contract"
    }
    generated_index_tokens: set[str] = set()
    projection_features: dict[str, set[object]] = {}
    projection_values: dict[str, set[str]] = {}
    component_records: list[dict[str, str]] = []

    def projection_lane(kind: str) -> str:
        return kind if kind in sequence_kinds else "normalized"

    for query_record in generated_queries or []:
        components = query_record.get("components")
        if not isinstance(components, list) or not components:
            raise ScanError(
                f"generated query lacks components: {query_record.get('task_id')}"
            )
        for component in components:
            kind = str(component["kind"])
            value = str(component["text"])
            if not value.strip():
                raise ScanError(
                    "generated query component is empty: "
                    f"{query_record.get('task_id')}/{kind}"
                )
            component_records.append({
                "task_id": str(query_record["task_id"]),
                "kind": kind,
                "text": value,
            })
            generated_index_tokens.update(token_set(norm(value)))
            if kind in indexed_component_kinds:
                lane = projection_lane(kind)
                projected = component_projection(kind, value)
                projection_values.setdefault(lane, set()).add(projected)
                projection_features.setdefault(lane, set()).update(
                    jaccard_features(projected, sequence=kind in sequence_kinds)
                )

    generated_token_postings: dict[str, set[int]] = {
        token: set() for token in generated_index_tokens
    }
    for record_index, record in enumerate(task_corpus):
        record_tokens = frozenset(WORD_RE.findall(record["normalized"]))
        for token in record_tokens & generated_index_tokens:
            generated_token_postings[token].add(record_index)

    projection_indexes: dict[
        str,
        tuple[list[str], dict[object, set[int]], dict[str, set[int]]],
    ] = {}

    def projection_index(
        kind: str,
    ) -> tuple[list[str], dict[object, set[int]], dict[str, set[int]]]:
        lane = projection_lane(kind)
        cached = projection_indexes.get(lane)
        if cached is not None:
            return cached
        projections: list[str] = []
        postings: dict[object, set[int]] = {}
        exact_postings: dict[str, set[int]] = {}
        sequence = kind in sequence_kinds
        wanted_features = projection_features.get(lane, set())
        wanted_values = projection_values.get(lane, set())
        for record_index, record in enumerate(task_corpus):
            projected = component_projection(kind, record["text"])
            projections.append(projected)
            if projected in wanted_values:
                exact_postings.setdefault(projected, set()).add(record_index)
            for feature in jaccard_features(projected, sequence=sequence):
                if feature in wanted_features:
                    postings.setdefault(feature, set()).add(record_index)
        cached = (projections, postings, exact_postings)
        projection_indexes[lane] = cached
        return cached

    generated_components = len(component_records)
    generated_component_hashes = [{
        "task_id": component["task_id"],
        "kind": component["kind"],
        "sha256": digest(component["text"].encode("utf-8")),
    } for component in component_records]

    def component_group(component: dict[str, str]) -> tuple[str, str]:
        kind = component["kind"]
        if kind in indexed_component_kinds:
            return ("indexed", projection_lane(kind))
        return ("direct", kind)

    # Retain only one corpus-wide derived projection lane at a time.  The
    # repository history includes large JSONL rows, so holding AST, CFG, API,
    # oracle, and normalized projections together can exceed the worker memory
    # limit.  This changes evaluation order only: candidates, thresholds, and
    # comparisons below are unchanged.
    ordered_queries = [{
        "task_id": component["task_id"],
        "components": [{
            "kind": component["kind"],
            "text": component["text"],
        }],
    } for _, component in sorted(
        enumerate(component_records),
        key=lambda item: (component_group(item[1]), item[0]),
    )]
    active_group: tuple[str, str] | None = None
    cached_functions = (
        norm, token_set, cpp_shape, cfg_shape, api_graph, test_oracle_shape,
    )
    for query_record in ordered_queries:
        query_id = str(query_record["task_id"])
        components = query_record.get("components")
        if not isinstance(components, list) or not components:
            raise ScanError(f"generated query lacks components: {query_id}")
        for component in components:
            kind = str(component["kind"])
            value = str(component["text"])
            group = component_group({
                "task_id": query_id,
                "kind": kind,
                "text": value,
            })
            if group != active_group:
                projection_indexes.clear()
                for cached_function in cached_functions:
                    cached_function.cache_clear()
                active_group = group
            stripped = value.strip()
            if not stripped:
                raise ScanError(f"generated query component is empty: {query_id}/{kind}")
            threshold = {
                "semantic_contract": 0.82, "oracle_behavior": 0.84,
                "hidden_test": 0.86, "test_oracle": 0.86,
                "mutation_family": 0.90, "api_graph": 0.92,
                "ast_shape": 0.90, "cfg_shape": 0.90,
            }.get(kind, NEAR_THRESHOLD)
            comparison_cutoff = max(0.75, threshold - 0.07)
            projected = component_projection(kind, value)
            indexed_projections: list[str] | None = None
            candidate_indices: set[int] = set()
            if kind in indexed_component_kinds:
                indexed_projections, postings, exact_postings = projection_index(kind)
                if projected:
                    candidate_indices.update(exact_postings.get(projected, set()))
                features = jaccard_features(
                    projected, sequence=kind in sequence_kinds
                )
                probe_count = overlap_probe_count(len(features), comparison_cutoff)
                probes = sorted(
                    features,
                    key=lambda feature: (
                        len(postings.get(feature, set())), repr(feature)
                    ),
                )[:probe_count]
                for feature in probes:
                    candidate_indices.update(postings.get(feature, set()))
                raw_tokens = token_set(norm(value))
                if raw_tokens:
                    raw_probe = min(
                        raw_tokens,
                        key=lambda token: (
                            len(generated_token_postings.get(token, set())), token
                        ),
                    )
                    candidate_indices.update(
                        generated_token_postings.get(raw_probe, set())
                    )
                else:
                    candidate_indices.update(range(len(task_corpus)))
            else:
                normalized_component = norm(value)
                component_tokens = token_set(normalized_component)
                rare_count = overlap_probe_count(
                    len(component_tokens), NEAR_THRESHOLD
                )
                rare_tokens = sorted(
                    component_tokens,
                    key=lambda token: (
                        len(generated_token_postings.get(token, set())), token
                    ),
                )[:rare_count]
                for token in rare_tokens:
                    candidate_indices.update(
                        generated_token_postings.get(token, set())
                    )
            for record_index in sorted(candidate_indices):
                record = task_corpus[record_index]
                record_text = record["text"]
                exact = (
                    stripped == record_text.strip()
                    or (len(stripped) >= 160 and stripped in record_text)
                )
                if exact:
                    matches["exact"].append({
                        "task_id": query_id,
                        "component": kind,
                        "path": record["path"],
                        "row": record["row"],
                    })
                record_projected = (
                    indexed_projections[record_index]
                    if indexed_projections is not None
                    else component_projection(kind, record_text)
                )
                structural_kind = kind in {"public_api", "api_graph", "target_source", "target_combined", "ast_shape", "cfg_shape"}
                semantic_kind = kind in {"hidden_test", "test_oracle", "oracle_behavior", "mutation_family", "semantic_contract"}
                minimum_tokens = 6 if kind == "cfg_shape" else 8
                if projected and projected == record_projected and len(projected.split()) >= minimum_tokens:
                    bucket = "structural" if structural_kind else "semantic" if semantic_kind else "exact"
                    matches[bucket].append({"task_id": query_id, "component": kind, "path": record["path"], "row": record["row"], "fingerprint_equal": True})
                    continue
                score = sequence_similarity(projected, record_projected) if kind in sequence_kinds else similarity(projected, record_projected)
                if score >= threshold:
                    bucket = "structural" if structural_kind else "semantic" if semantic_kind else "near"
                    matches[bucket].append({"task_id": query_id, "component": kind, "path": record["path"], "row": record["row"], "score": score, "threshold": threshold})
                elif score >= comparison_cutoff:
                    matches["ambiguous"].append({"task_id": query_id, "component": kind, "path": record["path"], "row": record["row"], "score": score, "threshold": threshold})
    complete = not parse_errors and not missing and not stale
    decision = "PASS" if complete and all(not value for value in matches.values()) else "FAIL"
    corpus_index = [{key: item[key] for key in ("path", "row", "sha256", "task_ids")} for item in task_corpus]
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA,
        "decision": decision,
        "repository_scope_complete": complete,
        "repository_root": str(root),
        "repository_revision": revision(root),
        "scanner_version": "charm-task-aware-uniqueness-v5",
        "normalization_version": "unicode-casefold-word-cpp-shape-v5",
        "parser_version": "python-json-jsonl-task-explosion-v5",
        "duplicate_policy_version": f"multi-fingerprint-v5-near-{NEAR_THRESHOLD}",
        "fingerprint_schema_version": "charm-problem-fingerprint-v5",
        "fingerprint_levels": ["raw", "normalized-contract", "starter", "api-graph", "ast-shape", "cfg-shape", "test-partition", "hidden-oracle", "mutation-family", "semantic-contract"],
        "ambiguity_collection_implemented": True,
        "stale_linked_worktrees_fail_closed": True,
        "scan_started_unix_ns": started,
        "scan_finished_unix_ns": time.time_ns(),
        "deterministic_seed": 0,
        "included_roots": [str(path) for path in roots],
        "unavailable_prunable_worktrees": stale,
        "exclusions": exclusions,
        "files_visited": files_visited,
        "text_files_inventoried": len(inventory),
        "classified_non_task_text_files": classified_non_task,
        "task_records_parsed": len(task_corpus),
        "parse_failures": len(parse_errors),
        "parse_failure_details": parse_errors,
        "proposal_plan_sha256": digest(plan_path.read_bytes()),
        "proposal_count": len(proposals),
        "generated_query_count": len(generated_queries or []),
        "generated_component_count": generated_components,
        "generated_component_index_sha256": digest(canonical(generated_component_hashes)),
        "proposals": [{"task_id": item["task_id"], "topic": item.get("topic"), "slot_id": item.get("slot_id"), "fingerprint_sha256": digest(canonical({field: item[field] for field in PROPOSAL_FIELDS}))} for item in proposals],
        "corpus_index_sha256": digest(canonical(corpus_index)),
        "task_id_matches": len(matches["task_id"]), "task_id_match_details": matches["task_id"],
        "exact_matches": len(matches["exact"]), "exact_match_details": matches["exact"],
        "near_matches": len(matches["near"]), "near_match_details": matches["near"],
        "structural_matches": len(matches["structural"]), "structural_match_details": matches["structural"],
        "semantic_matches": len(matches["semantic"]), "semantic_match_details": matches["semantic"],
        "ambiguous_matches": len(matches["ambiguous"]), "ambiguous_match_details": matches["ambiguous"],
        "linked_worktrees_reconciled": True,
        "active_archived_rejected_fixture_jsonl_registry_ledgers_included": True,
        "oversize_task_jsonl_exclusion_count": sum(
            item["path"].endswith(".jsonl")
            and item["reason"] == "opaque/oversize non-task payload"
            for item in exclusions
        ),
        "query_artifact_paths": sorted(str(path) for path in query),
        "scanner_source_sha256": digest(Path(__file__).read_bytes()),
    }
    receipt["receipt_sha256"] = digest(canonical(receipt))
    return receipt


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(canonical(value)); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        Path(temporary_name).unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposal-plan", required=True, type=Path)
    parser.add_argument("--proposal-artifact", action="append", default=[], type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--additional-root", action="append", default=[], type=Path)
    args = parser.parse_args(argv)
    if args.output.exists():
        print(f"refusing to overwrite receipt: {args.output}", file=sys.stderr); return 2
    try:
        receipt = scan(args.proposal_plan, args.output, args.root, args.additional_root, args.proposal_artifact)
    except ScanError as exc:
        receipt = {"schema_version": SCHEMA, "decision": "FAIL", "repository_scope_complete": False,
                   "parse_failures": 1, "task_id_matches": 0, "exact_matches": 0,
                   "near_matches": 0, "structural_matches": 0, "semantic_matches": 0,
                   "ambiguous_matches": 0, "errors": [str(exc)]}
    write(args.output, receipt)
    print(json.dumps({key: receipt.get(key) for key in ("decision", "files_visited", "task_records_parsed", "parse_failures", "task_id_matches", "exact_matches", "near_matches", "structural_matches", "semantic_matches", "ambiguous_matches")}, sort_keys=True))
    return 0 if receipt.get("decision") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
