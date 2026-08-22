#!/usr/bin/env python3
"""Build a deterministic failure inventory from the four SFT-v5 archives."""

from __future__ import annotations

import argparse
import json
import re
import tarfile
from collections import Counter, defaultdict
from pathlib import Path


TRIALS = ("a2", "a4", "a5", "a8")
RESULT_SUFFIX = "/.aider.results.json"
CHAT_SUFFIX = "/.aider.chat.history.md"


def read_members(archive: Path) -> tuple[dict[str, dict], dict[str, str]]:
    results: dict[str, dict] = {}
    chats: dict[str, str] = {}
    with tarfile.open(archive, "r:gz") as bundle:
        for member in bundle.getmembers():
            if not member.isfile():
                continue
            if member.name.endswith(RESULT_SUFFIX):
                handle = bundle.extractfile(member)
                if handle is None:
                    continue
                record = json.load(handle)
                results[record["testcase"]] = record
            elif member.name.endswith(CHAT_SUFFIX):
                handle = bundle.extractfile(member)
                if handle is None:
                    continue
                task = Path(member.name).parent.name
                chats[task] = handle.read().decode("utf-8", errors="replace")
    return results, chats


def terminal_block(chat: str) -> str:
    marker = "CMake Deprecation Warning"
    offset = chat.rfind(marker)
    if offset >= 0:
        return chat[offset:]
    return chat[-30_000:]


def terminal_symptom(record: dict, chat: str) -> str:
    outcomes = record["tests_outcomes"]
    if outcomes and outcomes[-1]:
        return "pass"

    block = terminal_block(chat)
    has_link_error = (
        "undefined reference" in block
        or "/usr/bin/ld:" in block
        or "collect2: error: ld returned" in block
    )
    has_compile_error = bool(
        re.search(r"^.+:\d+(?::\d+)?: (?:fatal )?error:", block, re.MULTILINE)
    )
    has_test_failure = " FAILED:" in block or bool(
        re.search(r"test cases:\s*\d+\s*\|.*\d+ failed", block)
    )

    if has_link_error:
        return "link_failure"
    if has_compile_error:
        return "compile_failure"
    if has_test_failure:
        return "test_or_runtime_failure"
    if (
        record["num_malformed_responses"]
        or record["num_exhausted_context_windows"]
        or record["num_error_outputs"]
    ):
        return "generation_or_transport_failure"
    return "unclassified_terminal_failure"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bundle",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Path to sft-v5-aiderfmt-1117-4trials",
    )
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()

    records: list[dict] = []
    per_task: dict[str, dict[str, object]] = defaultdict(
        lambda: {"pass_at_1": 0, "pass_at_2": 0, "turn_2_recoveries": 0, "trials": {}}
    )

    for trial in TRIALS:
        archive = args.bundle / "trials" / trial / "responses.tar.gz"
        trial_results, trial_chats = read_members(archive)
        if len(trial_results) != 26 or set(trial_results) != set(trial_chats):
            raise SystemExit(
                f"{trial}: expected 26 paired task records, got "
                f"{len(trial_results)} results and {len(trial_chats)} chats"
            )
        for task in sorted(trial_results):
            result = trial_results[task]
            outcomes = result["tests_outcomes"]
            passed_first = bool(outcomes[0])
            passed_any = any(outcomes)
            recovered = len(outcomes) > 1 and not outcomes[0] and outcomes[1]
            symptom = terminal_symptom(result, trial_chats[task])
            item = {
                "trial": trial,
                "task": task,
                "outcomes": outcomes,
                "passed_first": passed_first,
                "passed_any": passed_any,
                "turn_2_recovery": recovered,
                "terminal_symptom": symptom,
                "error_outputs": result["num_error_outputs"],
                "context_exhaustions": result["num_exhausted_context_windows"],
                "malformed_responses": result["num_malformed_responses"],
                "test_timeouts": result["test_timeouts"],
                "prompt_tokens": result["prompt_tokens"],
                "completion_tokens": result["completion_tokens"],
            }
            records.append(item)
            task_summary = per_task[task]
            task_summary["pass_at_1"] += int(passed_first)
            task_summary["pass_at_2"] += int(passed_any)
            task_summary["turn_2_recoveries"] += int(recovered)
            task_summary["trials"][trial] = {
                "outcomes": outcomes,
                "terminal_symptom": symptom,
            }

    terminal_failures = [item for item in records if not item["passed_any"]]
    symptom_counts = Counter(item["terminal_symptom"] for item in terminal_failures)
    report = {
        "schema_version": 1,
        "unit": "one two-turn task trajectory per task per trial",
        "headline": {
            "trajectories": len(records),
            "attempts": sum(len(item["outcomes"]) for item in records),
            "pass_at_1": sum(item["passed_first"] for item in records),
            "initial_failures": sum(not item["passed_first"] for item in records),
            "turn_2_recoveries": sum(item["turn_2_recovery"] for item in records),
            "pass_at_2": sum(item["passed_any"] for item in records),
            "terminal_failures": len(terminal_failures),
        },
        "terminal_failure_symptoms": dict(sorted(symptom_counts.items())),
        "overlapping_operational_flags": {
            "error_outputs": sum(item["error_outputs"] for item in records),
            "context_exhaustions": sum(item["context_exhaustions"] for item in records),
            "malformed_responses": sum(item["malformed_responses"] for item in records),
            "test_timeouts": sum(item["test_timeouts"] for item in records),
        },
        "per_task": dict(sorted(per_task.items())),
        "terminal_failure_records": terminal_failures,
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output_json:
        args.output_json.write_text(rendered)
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
