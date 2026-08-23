from __future__ import annotations

import argparse
import json
from pathlib import Path

from Reward_GRPO import multi_env_grpo
from Reward_GRPO import multi_env_verifier_runner


def test_config_has_seventeen_topics_and_sixty_seven_environments() -> None:
    config = multi_env_grpo.load_config()
    assert len(config["topics"]) == 17
    assert (
        sum(
            len(topic.get("dataset_policies", topic["live_policies"]))
            for topic in config["topics"]
        )
        == 67
    )
    assert all(set(topic["terminal_policies"]) <= set(topic["live_policies"]) for topic in config["topics"])
    global_topics = [topic for topic in config["topics"] if topic.get("runner_kind") == "global"]
    assert {topic["slug"] for topic in global_topics} == {
        "binary-search-tree",
        "kindergarten-garden",
        "linked-list",
        "meetup",
        "zebra-puzzle",
    }
    assert all(topic["dataset_policies"] == ["G01"] for topic in global_topics)
    assert all("G06" not in topic["live_policies"] for topic in global_topics)


def test_dataset_keeps_policy_metadata_out_of_model_prompt(tmp_path: Path) -> None:
    args = argparse.Namespace(
        tasks_dir=Path("Reward_GRPO"),
        out=tmp_path / "data",
        curriculum=multi_env_grpo.CURRICULUM_NAME,
        train_limit=None,
        eval_limit=17,
        eval_splits="validation,test",
        profile="multi-env-unit-test",
        run_id="multi-env-unit-test",
        sort_by_size=False,
        filter_train_oracle_full_marks=False,
        oracle_filter_workers=1,
        allow_non_gcc_curriculum=False,
        force=False,
    )
    paths = multi_env_grpo.build_data(args)
    rows = [json.loads(line) for line in paths["grpo_train"].read_text().splitlines()]
    assert len(rows) == 67
    prompts: dict[str, set[str]] = {}
    for row in rows:
        tags = row["metadata"]["tags"]
        topic = next(tag.split(":", 1)[1] for tag in tags if tag.startswith("strange-topic:"))
        prompts.setdefault(topic, set()).add(json.dumps(row["prompt"], sort_keys=True))
        assert any(tag.startswith("strange-policy:") for tag in tags)
    assert set(prompts) == {topic["slug"] for topic in multi_env_grpo.load_config()["topics"]}
    assert all(len(values) == 1 for values in prompts.values())
    manifest = json.loads(paths["manifest"].read_text())
    assert manifest["counts"] == {"available_shadow": 67, "monitor": 17, "train": 67, "validation": 0}
    assert manifest["split_contract"]["source_reference_answers_packaged"] is False


def test_bipolar_equal_policy_projection_requires_full_pass() -> None:
    receipt = {
        "full_pass": False,
        "policy_results": [
            {
                "status": "fail",
                "kernel_sum": 1,
                "kernel_total": 3,
                "kernels": [
                    {"kernel": 1},
                    {"kernel": 1},
                    {"kernel": -1},
                ],
            },
            {
                "status": "pass",
                "kernel_sum": 2,
                "kernel_total": 2,
                "kernels": [{"kernel": 1}, {"kernel": 1}],
            },
        ],
    }
    reward, passed, total = multi_env_grpo._project_reward(receipt, True)
    assert reward == (1 / 3 + 1) / 2
    assert (passed, total) == (4, 5)
    receipt["full_pass"] = True
    reward, _, _ = multi_env_grpo._project_reward(receipt, False)
    assert reward == 0.9


def test_runner_normalizes_both_receipt_schemas(tmp_path: Path) -> None:
    standard = tmp_path / "standard.json"
    standard.write_text(
        json.dumps(
            {
                "status": "fail",
                "kernel_results": [
                    {"kernel_id": "X-A", "kernel": 1, "status": "pass"},
                    {"kernel_id": "X-B", "kernel": -1, "status": "fail"},
                ],
            }
        )
    )
    normalized = multi_env_verifier_runner._normalize_receipt("E01", standard)
    assert normalized["status"] == "fail"
    assert normalized["kernel_sum"] == 0
    assert normalized["kernel_total"] == 2

    sublist = tmp_path / "sublist.json"
    sublist.write_text(
        json.dumps(
            {
                "status": "pass",
                "kernels": [
                    {"kernel_id": "5a", "kernel": 1, "verdict": "pass"},
                    {"kernel_id": "5x", "kernel": None, "verdict": "excluded"},
                ],
            }
        )
    )
    normalized = multi_env_verifier_runner._normalize_receipt("E05", sublist)
    assert normalized["status"] == "pass"
    assert normalized["kernel_sum"] == 1
    assert normalized["kernel_total"] == 1


def test_launch_is_pinned_to_phone_iter14_without_training_control_drift() -> None:
    yaml = Path("Reward_GRPO/multi_env_grpo_skypilot.yaml").read_text()
    assert "phone-number-kernel12-grpo20-spot-20260822-102653" in yaml
    assert "iter_0000014/adapter" in yaml
    assert "62fa190ad26e30fc1b5dd9543936ef549a49dd8cfa8220e4af726a1d499e575a" in yaml
    assert "MILES_EXPECTED_TRAIN_COUNT: \"67\"" in yaml
    assert "MILES_NUM_ROLLOUT: \"30\"" in yaml
    assert "iter_0000029/adapter" in yaml
    assert "MILES_N_SAMPLES_PER_PROMPT: \"32\"" in yaml
    assert "export MILES_APPLY_CHAT_TEMPLATE_KWARGS='{\"enable_thinking\": true}'" in yaml
    assert "use_spot: false" in yaml
