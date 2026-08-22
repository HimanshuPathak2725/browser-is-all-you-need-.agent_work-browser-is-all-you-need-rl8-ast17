from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Callable


Mutation = Callable[[dict[str, str]], None]
BASELINE_HASHES = {
    "clock.h": "74bb7ea77a1a11a856065976fbc421da450112df5e38e232b83c63e072c60c62",
    "clock.cpp": "f269249dfeae1939942a7f3335d9f058e8e1c0de7e74205d7cb44eb1d5822269",
}


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def replace_once(files: dict[str, str], filename: str, old: str, new: str) -> None:
    content = files[filename]
    if content.count(old) != 1:
        raise RuntimeError(f"expected one mutation target in {filename}: {old!r}")
    files[filename] = content.replace(old, new, 1)


def f01(files: dict[str, str]) -> None:
    replace_once(files, "clock.h", "    bool operator==(const clock& rhs) const;\n", "    bool operator==(const clock& rhs) const;\n    auto operator<=>(const clock& rhs) const = default;\n")


def f02(files: dict[str, str]) -> None:
    replace_once(files, "clock.cpp", "#include <iomanip>\n", "")


def f03(files: dict[str, str]) -> None:
    replace_once(files, "clock.h", "inline bool operator!=(const clock& lhs, const clock& rhs)\n{\n    return !(lhs == rhs);\n}\n\n", "")


def f04(files: dict[str, str]) -> None:
    replace_once(files, "clock.h", "    clock(int hour, int minute);\n", "")


def f05(files: dict[str, str]) -> None:
    replace_once(files, "clock.h", "inline bool operator!=", "bool operator!=")


def f06(files: dict[str, str]) -> None:
    replace_once(files, "clock.cpp", "#include <iomanip>\n", "#include <cstdio>\n")
    replace_once(
        files,
        "clock.cpp",
        "clock::operator string() const\n{\n    ostringstream str;\n    str << setw(2) << setfill('0') << hour_ << ':' << setw(2) << setfill('0') << minute_;\n    return str.str();\n}\n",
        "clock::operator string() const\n{\n    char buffer[5];\n    snprintf(buffer, sizeof(buffer), \"%02d:%02d\", hour_, minute_);\n    return string(buffer);\n}\n",
    )


def f07(files: dict[str, str]) -> None:
    replace_once(
        files,
        "clock.cpp",
        "clock::operator string() const\n{\n    ostringstream str;\n    str << setw(2) << setfill('0') << hour_ << ':' << setw(2) << setfill('0') << minute_;\n    return str.str();\n}\n",
        "clock::operator string() const\n{\n    return to_string(hour_) + \":\" + to_string(minute_);\n}\n",
    )


def f08(files: dict[str, str]) -> None:
    replace_once(files, "clock.cpp", "    hour_ %= hours_per_day;\n", "    if (hour_ > hours_per_day) hour_ %= hours_per_day;\n")


def f09(files: dict[str, str]) -> None:
    replace_once(files, "clock.cpp", "    minute_ += minutes;\n", "    minute_ += minutes + 1;\n")


def f10(files: dict[str, str]) -> None:
    replace_once(files, "clock.cpp", "    minute_ -= minutes;\n", "    (void)minutes;\n")


def f11(files: dict[str, str]) -> None:
    replace_once(files, "clock.cpp", "    return hour_ == rhs.hour_\n        && minute_ == rhs.minute_;\n", "    return hour_ == rhs.hour_;\n")


def f12(files: dict[str, str]) -> None:
    replace_once(files, "clock.cpp", "    return clock(hour, minute);\n", "    return clock(hour, minute + ((hour == 201 && minute == 3001) ? 1 : 0));\n")


def f13(files: dict[str, str]) -> None:
    replace_once(files, "clock.h", "    static clock at(int hour, int minute = 0);\n", "    static clock at(int hour, int minute);\n")


def f14(files: dict[str, str]) -> None:
    replace_once(files, "clock.h", "    bool operator==(const clock& rhs) const;\n", "    bool operator==(const clock& rhs) const;\n    bool operator!=(const clock& rhs) const;\n")
    replace_once(files, "clock.h", "inline bool operator!=(const clock& lhs, const clock& rhs)\n{\n    return !(lhs == rhs);\n}\n\n", "")
    replace_once(files, "clock.cpp", "bool clock::operator==(const clock& rhs) const\n{\n    return hour_ == rhs.hour_\n        && minute_ == rhs.minute_;\n}\n", "bool clock::operator==(const clock& rhs) const\n{\n    return hour_ == rhs.hour_\n        && minute_ == rhs.minute_;\n}\n\nbool clock::operator!=(const clock& rhs) const\n{\n    return !(*this == rhs);\n}\n")


SPECS: tuple[tuple[str, str, str, bool, Mutation], ...] = (
    ("f01_cxx20_spaceship", "language_mode", "Adds unsupported C++20 spaceship syntax to the C++17 header.", False, f01),
    ("f02_missing_iomanip", "dependency", "Removes the header declaring setw and setfill.", False, f02),
    ("f03_missing_inequality", "exact_api", "Deletes required operator!= entirely.", False, f03),
    ("f04_missing_constructor_declaration", "header_source", "Keeps constructor definitions but removes their class declaration.", False, f04),
    ("f05_noninline_header_operator", "odr_linkage", "Makes the header-defined free operator!= non-inline.", False, f05),
    ("f06_snprintf_warning", "warning_cleanliness", "Uses a five-byte snprintf buffer rejected by GCC -Werror.", False, f06),
    ("f07_unpadded_format", "formatting", "Renders H:M rather than zero-padded HH:MM.", False, f07),
    ("f08_negative_whole_day", "normalization", "Leaves exact whole-day values at 24:00.", False, f08),
    ("f09_plus_off_by_one", "arithmetic", "Adds one extra minute in plus().", False, f09),
    ("f10_minus_noop", "arithmetic_api", "minus() ignores its argument; official tests do not call minus directly.", True, f10),
    ("f11_equality_ignores_minutes", "equality", "Compares only hours and ignores minutes.", False, f11),
    ("f12_official_rare_case", "official_only", "Corrupts only official input (201, 3001).", False, f12),
    ("f13_missing_default_argument", "exact_api_default", "Removes the required default minute argument while preserving function type.", True, f13),
    ("f14_member_instead_of_free_inequality", "exact_api_operator_form", "Replaces required free operator!= with equivalent member behavior.", True, f14),
)


def parse_dataset_control(path: Path) -> tuple[dict[str, str], dict[str, object]]:
    selected: dict[str, object] | None = None
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("sample_id") == "a01-clock-turn2" and row.get("passed") is True:
                selected = row
                break
    if selected is None:
        raise RuntimeError("passed dataset control a01-clock-turn2 not found")
    response = str(selected["response"])
    blocks = {
        match.group(1): match.group(2) + "\n"
        for match in re.finditer(r"(?m)^(clock\.(?:h|cpp))\n```\n(.*?)\n```", response, re.DOTALL)
    }
    if set(blocks) != {"clock.h", "clock.cpp"}:
        raise RuntimeError(f"unexpected dataset control files: {sorted(blocks)}")
    metadata = {
        "sample_id": selected["sample_id"],
        "response_hash": selected["response_hash"],
        "score_output_hash": selected["score_output_hash"],
        "official_passed": True,
        "source": str(path),
    }
    return blocks, metadata


def write_candidate(root: Path, files: dict[str, str]) -> dict[str, str]:
    root.mkdir(parents=True)
    hashes: dict[str, str] = {}
    for filename in ("clock.h", "clock.cpp"):
        (root / filename).write_text(files[filename], encoding="utf-8")
        hashes[filename] = sha256_text(files[filename])
    return hashes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-jsonl", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    baseline_dir = root / "baseline/canonical"
    baseline = {name: (baseline_dir / name).read_text(encoding="utf-8") for name in ("clock.h", "clock.cpp")}
    observed_hashes = {name: sha256_text(content) for name, content in baseline.items()}
    if observed_hashes != BASELINE_HASHES:
        raise RuntimeError(f"canonical baseline hash mismatch: {observed_hashes}")
    samples_dir = root / "samples"
    controls_dir = root / "controls"
    for target in (samples_dir, controls_dir):
        if target.exists():
            shutil.rmtree(target)
        target.mkdir()
    samples: list[dict[str, object]] = []
    for sample_id, fault_class, description, official_expected_pass, mutate in SPECS:
        files = dict(baseline)
        mutate(files)
        hashes = write_candidate(samples_dir / sample_id, files)
        samples.append(
            {
                "sample_id": sample_id,
                "fault_class": fault_class,
                "description": description,
                "official_expected_pass": official_expected_pass,
                "strict_contract_expected_pass": False,
                "candidate_sha256": hashes,
            }
        )
    control_files, control_metadata = parse_dataset_control(args.dataset_jsonl.resolve())
    control_hashes = write_candidate(controls_dir / "dataset_official_pass", control_files)
    manifest = {
        "schema_version": 1,
        "task_id": "clock",
        "baseline": {
            "kind": "pinned_meta_reference",
            "candidate_sha256": observed_hashes,
            "accepted_by_original": True,
            "accepted_by_v2": True,
        },
        "dataset_control": {**control_metadata, "candidate_sha256": control_hashes, "included_in_fault_denominator": False},
        "sample_count": len(samples),
        "samples": samples,
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"sample_count": len(samples), "manifest": str(root / "manifest.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
