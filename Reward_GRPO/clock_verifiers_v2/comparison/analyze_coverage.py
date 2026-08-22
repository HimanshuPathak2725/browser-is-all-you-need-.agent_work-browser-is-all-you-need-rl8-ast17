from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ORIGINAL_POLICIES = {f"CL-E0{index}" for index in range(1, 6)}
V2_POLICIES = {f"CL2-C0{index}" for index in range(1, 9)}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def percentage(numerator: int, denominator: int) -> float:
    return round(100.0 * numerator / denominator, 2)


def similarity(left: set[str], right: set[str], universe: set[str]) -> dict[str, Any]:
    union = left | right
    intersection = left & right
    agreements = sum((item in left) == (item in right) for item in universe)
    return {
        "intersection_count": len(intersection),
        "union_count": len(union),
        "jaccard_percent": percentage(len(intersection), len(union)) if union else 100.0,
        "binary_agreement_percent": percentage(agreements, len(universe)),
        "original_only": sorted(left - right),
        "v2_only": sorted(right - left),
    }


def result_index(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items = document.get("results", document.get("candidates"))
    if not isinstance(items, list):
        raise RuntimeError("result document has neither results nor candidates list")
    return {str(item["candidate_id"]): item for item in items}


def validate_document(
    document: dict[str, Any],
    path: Path,
    manifest_hash: str,
    expected_candidates: set[str],
    expected_policies: set[str],
) -> dict[str, dict[str, Any]]:
    if document.get("manifest_sha256") != manifest_hash:
        raise RuntimeError(f"{path}: stale manifest hash {document.get('manifest_sha256')}")
    indexed = result_index(document)
    if set(indexed) != expected_candidates:
        raise RuntimeError(f"{path}: candidate set mismatch")
    for candidate_id, item in indexed.items():
        policies = {policy["policy_id"] for policy in item["policies"]}
        if policies != expected_policies:
            raise RuntimeError(f"{path}: {candidate_id} policy set mismatch: {sorted(policies)}")
        statuses = {str(policy["status"]).upper() for policy in item["policies"]}
        if not statuses <= {"PASS", "FAIL", "INVALID"}:
            raise RuntimeError(f"{path}: {candidate_id} unknown statuses: {statuses}")
        if item.get("invalid") or item.get("invalid_flag") or "INVALID" in statuses:
            raise RuntimeError(f"{path}: {candidate_id} is INVALID")
        expected_suite_pass = all(str(policy["status"]).upper() == "PASS" for policy in item["policies"])
        if bool(item["suite_pass"]) != expected_suite_pass:
            raise RuntimeError(f"{path}: {candidate_id} inconsistent suite_pass")
        if bool(item["suite_detected"]) == expected_suite_pass:
            raise RuntimeError(f"{path}: {candidate_id} inconsistent suite_detected")
    return indexed


def policy_statuses(item: dict[str, Any]) -> dict[str, str]:
    return {str(policy["policy_id"]): str(policy["status"]).upper() for policy in item["policies"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    root = Path(__file__).resolve().parent
    parser.add_argument("--manifest", type=Path, default=root / "manifest.json")
    parser.add_argument("--original", type=Path, default=root / "results/original_results.json")
    parser.add_argument("--v2", type=Path, default=root / "results/v2_results.json")
    parser.add_argument("--output", type=Path, default=root / "results/coverage_summary.json")
    args = parser.parse_args()

    manifest = load(args.manifest)
    original = load(args.original)
    v2 = load(args.v2)
    manifest_hash = sha256(args.manifest)
    sample_specs = {sample["sample_id"]: sample for sample in manifest["samples"]}
    faulty_ids = set(sample_specs)
    original_control_ids = {"canonical_baseline", "dataset_official_pass"}
    v2_control_ids = {"canonical_baseline", str(manifest["dataset_control"]["sample_id"])}
    original_index = validate_document(
        original, args.original, manifest_hash, faulty_ids | original_control_ids, ORIGINAL_POLICIES
    )
    v2_index = validate_document(v2, args.v2, manifest_hash, faulty_ids | v2_control_ids, V2_POLICIES)

    original_suite = {item for item in faulty_ids if original_index[item]["suite_detected"]}
    v2_suite = {item for item in faulty_ids if v2_index[item]["suite_detected"]}
    original_shaping = {item for item in faulty_ids if original_index[item]["shaping_detected"]}
    v2_shaping = {item for item in faulty_ids if v2_index[item]["shaping_detected"]}
    original_terminal = {
        item for item in faulty_ids if str(original_index[item]["terminal_status"]).upper() == "FAIL"
    }
    v2_terminal = {
        item for item in faulty_ids if str(v2_index[item]["terminal_status"]).upper() == "FAIL"
    }

    rows: list[dict[str, Any]] = []
    for sample_id in sorted(faulty_ids):
        spec = sample_specs[sample_id]
        original_status = policy_statuses(original_index[sample_id])
        v2_status = policy_statuses(v2_index[sample_id])
        expected_terminal_pass = bool(spec["official_expected_pass"])
        observed_terminal_passes = {
            "original": original_status["CL-E03"] == "PASS",
            "v2": v2_status["CL2-C08"] == "PASS",
        }
        if any(value != expected_terminal_pass for value in observed_terminal_passes.values()):
            raise RuntimeError(
                f"{sample_id}: terminal observations {observed_terminal_passes} disagree with manifest expectation {expected_terminal_pass}"
            )
        rows.append(
            {
                "sample_id": sample_id,
                "fault_class": spec["fault_class"],
                "official_expected_pass": expected_terminal_pass,
                "original_detected": sample_id in original_suite,
                "original_failed_policies": sorted(
                    policy_id for policy_id, status in original_status.items() if status == "FAIL"
                ),
                "original_terminal": original_status["CL-E03"],
                "v2_detected": sample_id in v2_suite,
                "v2_failed_policies": sorted(
                    policy_id for policy_id, status in v2_status.items() if status == "FAIL"
                ),
                "v2_terminal": v2_status["CL2-C08"],
            }
        )

    denominator = len(faulty_ids)
    summary = {
        "schema_version": 1,
        "manifest_sha256": manifest_hash,
        "fault_denominator": denominator,
        "invalid_candidate_count": 0,
        "coverage": {
            "original_full_suite": {
                "detected": len(original_suite),
                "percent": percentage(len(original_suite), denominator),
                "missed": sorted(faulty_ids - original_suite),
            },
            "v2_full_suite": {
                "detected": len(v2_suite),
                "percent": percentage(len(v2_suite), denominator),
                "missed": sorted(faulty_ids - v2_suite),
            },
            "original_shaping": {
                "detected": len(original_shaping),
                "percent": percentage(len(original_shaping), denominator),
                "missed": sorted(faulty_ids - original_shaping),
            },
            "v2_shaping": {
                "detected": len(v2_shaping),
                "percent": percentage(len(v2_shaping), denominator),
                "missed": sorted(faulty_ids - v2_shaping),
            },
            "original_terminal": {
                "detected": len(original_terminal),
                "percent": percentage(len(original_terminal), denominator),
                "missed": sorted(faulty_ids - original_terminal),
            },
            "v2_terminal": {
                "detected": len(v2_terminal),
                "percent": percentage(len(v2_terminal), denominator),
                "missed": sorted(faulty_ids - v2_terminal),
            },
        },
        "similarity": {
            "full_suite": similarity(original_suite, v2_suite, faulty_ids),
            "shaping": similarity(original_shaping, v2_shaping, faulty_ids),
            "terminal": similarity(original_terminal, v2_terminal, faulty_ids),
        },
        "controls": {},
        "samples": rows,
        "evidence": {
            "original_results": str(args.original.resolve()),
            "original_results_sha256": sha256(args.original),
            "v2_results": str(args.v2.resolve()),
            "v2_results_sha256": sha256(args.v2),
        },
    }
    control_pairs = {
        "canonical_baseline": ("canonical_baseline", "canonical_baseline"),
        "dataset_official_pass": ("dataset_official_pass", str(manifest["dataset_control"]["sample_id"])),
    }
    for label, (original_id, v2_id) in control_pairs.items():
        original_control_status = policy_statuses(original_index[original_id])
        v2_control_status = policy_statuses(v2_index[v2_id])
        summary["controls"][label] = {
            "original_candidate_id": original_id,
            "original_suite_pass": bool(original_index[original_id]["suite_pass"]),
            "original_terminal": str(original_index[original_id]["terminal_status"]).upper(),
            "original_failed_policies": sorted(
                policy_id for policy_id, status in original_control_status.items() if status == "FAIL"
            ),
            "v2_candidate_id": v2_id,
            "v2_suite_pass": bool(v2_index[v2_id]["suite_pass"]),
            "v2_terminal": str(v2_index[v2_id]["terminal_status"]).upper(),
            "v2_failed_policies": sorted(
                policy_id for policy_id, status in v2_control_status.items() if status == "FAIL"
            ),
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output.resolve()), "coverage": summary["coverage"], "similarity": summary["similarity"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
