#!/usr/bin/env python3
import collections
import json
from pathlib import Path


ROOT = Path("/tmp/phone_iter14_gcs_audit/extracted")


def top(counter, limit=5):
    return [{"value": key, "count": count} for key, count in counter.most_common(limit)]


def rate(numerator, denominator):
    return round(numerator / denominator, 6) if denominator else 0.0


def summarize_stage(stage):
    path = ROOT / f"{stage}_records.jsonl"
    grouped = collections.defaultdict(list)
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                grouped[int(row["rollout_id"])].append(row)

    updates = []
    total_reasons = collections.Counter()
    total_failed_reasons = collections.Counter()
    total_tasks = collections.Counter()
    total_signatures = collections.Counter()
    total_kernels = collections.Counter()
    total_flags = collections.Counter()
    for rollout_id in sorted(grouped):
        records = grouped[rollout_id]
        reasons = collections.Counter(str(row.get("reason") or "missing") for row in records)
        passed = sum(row.get("all_tests_pass") is True for row in records)
        failed = [row for row in records if row.get("all_tests_pass") is not True]
        passed_rows = [row for row in records if row.get("all_tests_pass") is True]
        failed_reasons = collections.Counter(
            str(row.get("reason") or "missing") for row in failed
        )
        tasks = collections.Counter(
            str(row.get("task_id") or row.get("problem_id") or "missing") for row in failed
        )
        signatures = collections.Counter(
            str(row.get("failure_signature") or "missing") for row in failed
        )
        kernels = collections.Counter()
        for row in failed:
            for kernel in row.get("kernel_results") or []:
                if not isinstance(kernel, dict):
                    continue
                if kernel.get("status") not in ("pass", "passed") or kernel.get("kernel") == -1:
                    kernels[str(kernel.get("kernel_id") or "missing")] += 1
        flags = {
            "compile_error": sum(bool(row.get("compile_error")) for row in failed),
            "format_invalid": sum(row.get("format_valid") is False for row in failed),
            "timeout": sum(bool(row.get("timeout")) for row in failed),
            "infrastructure_error": sum(bool(row.get("infrastructure_error")) for row in failed),
            "truncated": sum(row.get("sample_status") == "truncated" for row in failed),
            "response_at_limit": sum(
                isinstance(row.get("response_length"), int) and row["response_length"] >= 8192
                for row in failed
            ),
            "passed_format_invalid": sum(
                row.get("format_valid") is False for row in passed_rows
            ),
            "passed_truncated": sum(
                row.get("sample_status") == "truncated" for row in passed_rows
            ),
        }
        total_reasons.update(reasons)
        total_failed_reasons.update(failed_reasons)
        total_tasks.update(tasks)
        total_signatures.update(signatures)
        total_kernels.update(kernels)
        total_flags.update(flags)
        updates.append(
            {
                "rollout_id": rollout_id,
                "records": len(records),
                "passes": passed,
                "failures": len(records) - passed,
                "pass_rate": rate(passed, len(records)),
                "failure_rate": rate(len(records) - passed, len(records)),
                "native_reason_counts": dict(sorted(reasons.items())),
                "native_failed_reason_counts": dict(sorted(failed_reasons.items())),
                **flags,
                "dominant_failed_tasks": top(tasks),
                "dominant_failure_signatures": top(signatures),
                "dominant_failed_kernel_ids": top(kernels, 10),
            }
        )

    records = sum(item["records"] for item in updates)
    passes = sum(item["passes"] for item in updates)
    first = updates[:5]
    last = updates[-5:]
    first_rate = rate(sum(item["passes"] for item in first), sum(item["records"] for item in first))
    last_rate = rate(sum(item["passes"] for item in last), sum(item["records"] for item in last))
    best = max(item["pass_rate"] for item in updates)
    worst = min(item["pass_rate"] for item in updates)
    return {
        "records_path": str(path),
        "task_scope": (
            "8 Phone Number shadow-training tasks"
            if stage == "train"
            else "8-task Phone Number training monitor (not Fixed26)"
        ),
        "totals": {
            "records": records,
            "passes": passes,
            "failures": records - passes,
            "pass_rate": rate(passes, records),
            "failure_rate": rate(records - passes, records),
            **dict(total_flags),
            "native_reason_counts": dict(sorted(total_reasons.items())),
            "native_failed_reason_counts": dict(sorted(total_failed_reasons.items())),
            "dominant_failed_tasks": top(total_tasks, 10),
            "dominant_failure_signatures": top(total_signatures, 10),
            "dominant_failed_kernel_ids": top(total_kernels, 15),
        },
        "trend": {
            "first_five_updates_pass_rate": first_rate,
            "last_five_updates_pass_rate": last_rate,
            "last_minus_first_percentage_points": round((last_rate - first_rate) * 100, 3),
            "best_updates": [item["rollout_id"] for item in updates if item["pass_rate"] == best],
            "best_pass_rate": best,
            "worst_updates": [item["rollout_id"] for item in updates if item["pass_rate"] == worst],
            "worst_pass_rate": worst,
        },
        "updates": updates,
    }


stages = {stage: summarize_stage(stage) for stage in ("train", "eval")}
anomalies = []
for stage, data in stages.items():
    totals = data["totals"]
    for key in ("infrastructure_error", "timeout", "compile_error", "format_invalid"):
        if totals[key]:
            anomalies.append(
                {
                    "stage": stage,
                    "kind": key,
                    "count": totals[key],
                    "severity": "critical" if key != "format_invalid" else "model_failure",
                }
            )
    if totals["truncated"]:
        anomalies.append(
            {
                "stage": stage,
                "kind": "generation_truncated",
                "count": totals["truncated"],
                "severity": "critical_context_risk",
                "note": "Native sample_status=truncated; no explicit context_exhaustion field exists.",
            }
        )
    if totals["passed_format_invalid"]:
        anomalies.append(
            {
                "stage": stage,
                "kind": "passed_with_format_valid_false",
                "count": totals["passed_format_invalid"],
                "severity": "integrity_nuance",
                "note": (
                    "These rows have all_tests_pass=true despite format_valid=false; treat as a "
                    "verifier-field inconsistency/partial-reward nuance, not failed outputs."
                ),
            }
        )
    if totals["passed_truncated"]:
        anomalies.append(
            {
                "stage": stage,
                "kind": "passed_with_truncated_status",
                "count": totals["passed_truncated"],
                "severity": "integrity_nuance",
                "note": "Excluded from the failed-truncation count because all_tests_pass=true.",
            }
        )

report = {
    "run_id": "phone-number-kernel12-grpo20-spot-20260822-102653",
    "schema_version": 1,
    "identifier_semantics": {
        "native_epoch_field": False,
        "native_iteration_field": False,
        "native_rollout_id": (
            "payload rollout_id and grpo[_eval]_<id>.pt filename suffix, zero-based 0..19"
        ),
        "checkpoint_iteration": (
            "separate checkpoint directories iter_0000004, iter_0000009, "
            "iter_0000014, iter_0000019"
        ),
        "derived_jsonl_iteration": (
            "copied verbatim from native rollout_id; this does not assert a native epoch field"
        ),
    },
    "stages": stages,
    "critical_anomalies": anomalies,
}
(ROOT / "per_update_failure_report.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)

lines = [
    "# Phone Number GRPO per-update failure report",
    "",
    "The native artifacts have no epoch or iteration field. They encode a zero-based "
    "`rollout_id` in both the PT payload and `grpo[_eval]_<id>.pt` filename (0–19). "
    "Checkpoints are separate and saved at iterations 4, 9, 14, and 19.",
    "",
    "The eval rows here are the 8-task Phone Number training monitor, not the four Fixed26 runs.",
]
for stage in ("train", "eval"):
    data = stages[stage]
    totals = data["totals"]
    trend = data["trend"]
    lines.extend(
        [
            "",
            f"## {stage.title()}",
            "",
            "Scope: {}. Overall {}/{} passed ({:.1%}); first-five to last-five "
            "pass-rate delta {:+.3f} pp.".format(
                data["task_scope"],
                totals["passes"],
                totals["records"],
                totals["pass_rate"],
                trend["last_minus_first_percentage_points"],
            ),
            "",
            "| Update | Pass | Fail | Pass rate | Failed compile | Failed format invalid | "
            "Failed timeout | Failed infra | Failed truncated | Dominant failed native reason | "
            "Dominant failed task | Dominant signature | "
            "Dominant failed kernel |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|",
        ]
    )
    for item in data["updates"]:
        reason = max(
            item["native_failed_reason_counts"].items(),
            key=lambda pair: (pair[1], pair[0]),
        )
        task = item["dominant_failed_tasks"][0] if item["dominant_failed_tasks"] else {"value": "—", "count": 0}
        signature = item["dominant_failure_signatures"][0] if item["dominant_failure_signatures"] else {"value": "—", "count": 0}
        kernel = item["dominant_failed_kernel_ids"][0] if item["dominant_failed_kernel_ids"] else {"value": "—", "count": 0}
        lines.append(
            "| {} | {} | {} | {:.1%} | {} | {} | {} | {} | {} | `{}` ({}) | `{}` ({}) | "
            "`{}` ({}) | `{}` ({}) |".format(
                item["rollout_id"], item["passes"], item["failures"], item["pass_rate"],
                item["compile_error"], item["format_invalid"], item["timeout"],
                item["infrastructure_error"], item["truncated"], reason[0], reason[1],
                task["value"], task["count"], signature["value"], signature["count"],
                kernel["value"], kernel["count"],
            )
        )
    lines.extend(
        [
            "",
            "Best update(s): {} at {:.1%}; worst: {} at {:.1%}.".format(
                trend["best_updates"], trend["best_pass_rate"],
                trend["worst_updates"], trend["worst_pass_rate"],
            ),
            "",
            "Native reason totals: "
            + ", ".join(f"`{key}`={value}" for key, value in totals["native_reason_counts"].items())
            + ".",
            "",
            "Native failed-reason totals: "
            + ", ".join(
                f"`{key}`={value}" for key, value in totals["native_failed_reason_counts"].items()
            )
            + ".",
            "",
            "Dominant failed tasks: "
            + ", ".join("`{}`={}".format(x["value"], x["count"]) for x in totals["dominant_failed_tasks"][:5])
            + ".",
            "",
            "Dominant failure signatures: "
            + ", ".join("`{}`={}".format(x["value"], x["count"]) for x in totals["dominant_failure_signatures"][:5])
            + ".",
            "",
            "Dominant failed kernels: "
            + ", ".join("`{}`={}".format(x["value"], x["count"]) for x in totals["dominant_failed_kernel_ids"][:8])
            + ".",
        ]
    )

lines.extend(["", "## Critical anomalies", ""])
for item in anomalies:
    lines.append(
        "- `{}` `{}`: {} rows. {}".format(
            item["stage"], item["kind"], item["count"], item.get("note", "")
        ).rstrip()
    )
if not anomalies:
    lines.append("No compile, timeout, infrastructure, format, or truncation anomalies were observed.")
(ROOT / "per_update_failure_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

print(json.dumps({stage: {"totals": stages[stage]["totals"], "trend": stages[stage]["trend"]} for stage in stages}, indent=2))
print(json.dumps(anomalies, indent=2))
