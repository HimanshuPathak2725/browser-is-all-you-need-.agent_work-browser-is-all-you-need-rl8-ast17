from __future__ import annotations

import json
import re
from pathlib import Path


LEDGER = Path("docs/aider_posttraining_runs.json")
FINAL_RECEIPT = Path("docs/receipts/glm47-aider-rl-v2-fixed26-run-receipt.json")
DATA_PUBLICATION = Path(
    "docs/receipts/glm47-aider-gated-data-publication.json"
)
README = Path("README.md")


def test_aider_progress_ledger_matches_final_rl_receipt() -> None:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    receipt = json.loads(FINAL_RECEIPT.read_text(encoding="utf-8"))
    rl = next(stage for stage in ledger["stages"] if stage["id"] == "rl-v2")

    assert receipt["status"] == "complete"
    assert rl["adapter_sha256"] == receipt["adapter_sha256"]
    assert rl["training"]["dataset_manifest_sha256"] == receipt[
        "training_data_manifest_sha256"
    ]
    assert rl["pass_at_1"] == receipt["validation"]["pass_at_1"] == 1
    assert rl["pass_at_2"] == receipt["validation"]["pass_at_k"] == 6
    assert rl["well_formed_tasks"] == receipt["validation"]["well_formed_tasks"] == 26


def test_aider_progress_ledger_has_the_promoted_lineage_only() -> None:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert [stage["id"] for stage in ledger["stages"]] == [
        "base",
        "sft-v1",
        "sft-v2",
        "sft-v3",
        "rl-v2",
    ]


def test_aider_catalog_maps_every_preserved_dataset_and_eval() -> None:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    publication = json.loads(DATA_PUBLICATION.read_text(encoding="utf-8"))
    expected_datasets = {
        "sft-v1-321",
        "sft-v2-1211",
        "curated-heuristic-v1",
        "curated-high-confidence-v1",
        "signal-v2",
        "signal-v3",
        "sft-gold-v4",
        "reverify-715",
        "raw-concat-v1",
        "combined-v5-500",
        "combined-v5-build-workbench",
        "sft-v3-complement-530",
        "pass1-skills-600",
        "reverify-audit",
        "regression-audit",
        "rl-shadow-replay-253",
        "rl-shadow-difficulty-20260722",
        "rl-v2-shadow-169",
        "rl-shadow-253-july21",
    }
    expected_evaluations = {
        "base",
        "sft-v1",
        "sft-v2",
        "signal-v3",
        "gold-v4",
        "raw-concat-v1",
        "combined-v5",
        "sft-v3",
        "pass1-skills-600",
        "rl-july21-iter2",
        "merged-sft",
        "rl-v2-iter0",
        "rl-v2",
    }

    assert publication["status"] == "passed"
    assert publication["data_entries"] == len(ledger["dataset_catalog_paths"]) == 19
    assert publication["evaluation_entries"] == len(
        ledger["evaluation_catalog_paths"]
    ) == 13
    assert set(ledger["dataset_catalog_paths"]) == expected_datasets
    assert set(ledger["evaluation_catalog_paths"]) == expected_evaluations
    assert publication["data"]["private"] is True
    assert publication["data"]["gated"] == "manual"
    assert publication["data"]["roundtrip"] == "passed"
    assert publication["evaluations"]["private"] is True
    assert publication["evaluations"]["gated"] == "manual"
    assert publication["evaluations"]["roundtrip"] == "passed"
    assert (
        ledger["artifact_catalogs"]["training_and_audit_data"]["revision"]
        == publication["data"]["revision"]
    )
    assert (
        ledger["artifact_catalogs"]["fixed26_responses"]["revision"]
        == publication["evaluations"]["revision"]
    )
    assert (
        ledger["artifact_catalogs"]["training_and_audit_data"][
            "upload_manifest_sha256"
        ]
        == publication["data"]["upload_manifest_sha256"]
    )
    assert (
        ledger["artifact_catalogs"]["fixed26_responses"][
            "upload_manifest_sha256"
        ]
        == publication["evaluations"]["upload_manifest_sha256"]
    )


def test_shadow_corpus_is_labeled_as_runtime_oracle() -> None:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    shadow = ledger["shadow_rl_corpus"]

    assert shadow["access_tier"] == "runtime-oracle"
    assert shadow["contains_rubrics"] is True
    assert shadow["contains_hidden_executable_tests"] is True


def test_readme_local_links_exist() -> None:
    text = README.read_text(encoding="utf-8")
    for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
        if "://" in target:
            continue
        path = Path(target.split("#", 1)[0])
        assert path.exists(), target
