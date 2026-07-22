from pathlib import Path


GRPO_RUNNER = Path("scripts/train_grpo.sh")


def test_grpo_receipt_records_optional_continuation_provenance() -> None:
    text = GRPO_RUNNER.read_text(encoding="utf-8")
    assignments = {
        "GRPO_CONTINUATION_MODE": "MILES_GRPO_CONTINUATION_MODE",
        "GRPO_PARENT_RUN_ID": "MILES_GRPO_PARENT_RUN_ID",
        "GRPO_PARENT_ITERATION": "MILES_GRPO_PARENT_ITERATION",
        "GRPO_PARENT_ADAPTER_SHA256": "MILES_GRPO_PARENT_ADAPTER_SHA256",
    }
    receipt_fields = {
        "grpo_continuation_mode": "GRPO_CONTINUATION_MODE",
        "grpo_parent_run_id": "GRPO_PARENT_RUN_ID",
        "grpo_parent_iteration": "GRPO_PARENT_ITERATION",
        "grpo_parent_adapter_sha256": "GRPO_PARENT_ADAPTER_SHA256",
    }

    for local_name, environment_name in assignments.items():
        assert f'{local_name}="${{{environment_name}:-none}}"' in text
    for field, local_name in receipt_fields.items():
        assert f"{field}=${{{local_name}}}" in text

    receipt_start = text.index('cat >"${RUN_RECEIPT}" <<EOF')
    receipt_end = text.index("\nEOF", receipt_start)
    receipt = text[receipt_start:receipt_end]
    for field in receipt_fields:
        assert f"{field}=" in receipt

    assert "weights_only_fresh_optimizer)" in text
    assert "continuation parent SHA-256 must equal" in text
    assert "GRPO parent provenance requires a non-none continuation mode" in text
    assert "weights-only continuation requires a pinned native reconstruction manifest" in text
    assert "expected_native_reconstruction_manifest_sha256=" in receipt
