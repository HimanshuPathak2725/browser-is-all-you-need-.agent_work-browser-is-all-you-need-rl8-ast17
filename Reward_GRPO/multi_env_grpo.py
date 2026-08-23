"""Multi-topic GRPO curriculum backed by validated Strange policy environments.

The model sees only the pinned official instructions and starter files.  Policy
IDs live in task metadata and the selected verifier plus required terminal
policies run in a separate, network-disabled GCC 13.3 container.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import shutil
import subprocess
import threading
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Sequence

from glm47_posttraining.aider_polyglot.dataset import (
    SOURCE_MANIFEST_KIND,
    build_aider_polyglot_datasets,
)
from glm47_posttraining.aider_polyglot.harness import (
    CandidatePolicyError,
    _validate_candidate_source,
)
from glm47_posttraining.aider_polyglot.parser import (
    AiderResponseError,
    parse_whole_file_response,
)
from glm47_posttraining.aider_polyglot.schema import AiderPolyglotTask, AiderShadowRubric
from glm47_posttraining.integrations.miles_aider_polyglot import (
    neutralize_infrastructure_scores,
    run_response_contract_preflight,
)


CURRICULUM_NAME = "multi-env-strange-v1"
DATASET_KIND = "aider-polyglot-cpp-shadow-grpo"
POLYGLOT_COMMIT = "7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f"
REWARD_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = REWARD_ROOT / "multi_env_grpo_config.json"
FIXTURE_ROOT = REWARD_ROOT / "multi_env_fixtures"
PROMPT_ROOT = REWARD_ROOT / "multi_env_prompts"
DOCKERFILE_PATH = REWARD_ROOT / "multi_env_verifier.Dockerfile"
RUNNER_PATH = REWARD_ROOT / "multi_env_verifier_runner.py"
DEFAULT_WORKERS = 24
DEFAULT_TIMEOUT_SECONDS = 900
_ACTIVE_WORKERS = 0
_ACTIVE_WORKERS_LOCK = threading.Lock()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode()
        data = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def load_config() -> dict[str, Any]:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if config.get("schema_version") != 1:
        raise ValueError("unsupported multi-environment config schema")
    topics = config.get("topics")
    if not isinstance(topics, list):
        raise ValueError("multi-environment config has no topics")
    slugs = [str(topic.get("slug")) for topic in topics]
    if len(slugs) != len(set(slugs)):
        raise ValueError("multi-environment topic slugs are not unique")
    policy_count = 0
    for topic in topics:
        live = [str(value) for value in topic.get("live_policies", [])]
        terminal = [str(value) for value in topic.get("terminal_policies", [])]
        if not live or len(live) != len(set(live)) or not set(terminal).issubset(live):
            raise ValueError(f"invalid policy selection for {topic.get('slug')}")
        policy_count += len(live)
    if len(topics) != int(config["expected_topic_count"]):
        raise ValueError("multi-environment topic count does not match its contract")
    if policy_count != int(config["expected_train_count"]):
        raise ValueError("multi-environment policy count does not match its contract")
    return config


def _topic_by_slug(slug: str) -> dict[str, Any]:
    config = load_config()
    return next(topic for topic in config["topics"] if topic["slug"] == slug)


def _ordered_policies(topic: dict[str, Any]) -> list[str]:
    terminal = [str(value) for value in topic["terminal_policies"]]
    return [*terminal, *(str(value) for value in topic["live_policies"] if value not in terminal)]


def _verifier_script(topic: dict[str, Any], policy: str) -> Path:
    number = int(policy[1:])
    matches = sorted(
        (REWARD_ROOT / str(topic["package"]) / "verifiers").glob(
            f"verifier_{number:02d}_*.py"
        )
    )
    if len(matches) != 1 or matches[0].is_symlink():
        raise ValueError(
            f"expected one verifier script for {topic['slug']} {policy}, found {len(matches)}"
        )
    return matches[0]


def _validate_fixture(topic: dict[str, Any]) -> Path:
    fixture = FIXTURE_ROOT / str(topic["slug"])
    if not fixture.is_dir() or fixture.is_symlink():
        raise ValueError(f"missing regular fixture for {topic['slug']}")
    required = {
        ".docs/instructions.md",
        "CMakeLists.txt",
        *(str(value) for value in topic["editable_files"]),
    }
    for relative in required:
        path = fixture / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"unsafe or missing fixture asset: {topic['slug']}/{relative}")
    if any(path.name.startswith(".aider") for path in fixture.rglob("*")):
        raise ValueError(f"evaluation history leaked into fixture: {topic['slug']}")
    if topic.get("runner_kind") == "sublist":
        manifest = fixture / ".meta" / "glm47_task.json"
        if not manifest.is_file() or manifest.is_symlink():
            raise ValueError("Sublist fixture is missing its pinned task manifest")
    return fixture


def _prompt_instructions(topic: dict[str, Any]) -> Path:
    path = PROMPT_ROOT / str(topic["slug"]) / "instructions.md"
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"missing original prompt instructions for {topic['slug']}")
    return path


def _write_task_source(output: Path) -> Path:
    config = load_config()
    practice = output / "cpp" / "exercises" / "practice"
    practice.mkdir(parents=True)
    overlap: list[str] = []
    for topic in config["topics"]:
        fixture = _validate_fixture(topic)
        slug = str(topic["slug"])
        overlap.append(slug)
        terminal = set(str(value) for value in topic["terminal_policies"])
        for ordinal, policy in enumerate(_ordered_policies(topic)):
            exercise_name = f"{slug}--{ordinal:02d}-{policy.lower()}"
            exercise = practice / exercise_name
            docs = exercise / ".docs"
            docs.mkdir(parents=True)
            instructions = _prompt_instructions(topic).read_bytes()
            (docs / "instructions.md").write_bytes(instructions)
            for name in topic["editable_files"]:
                shutil.copy2(fixture / str(name), exercise / str(name))
            hidden_name = "multi_env_hidden_test.cpp"
            hidden = (
                "// Dataset-integrity placeholder; live reward uses the isolated Strange pack.\n"
                f"// topic={slug} policy={policy}\n"
                "int main() { return 0; }\n"
            ).encode()
            (exercise / hidden_name).write_bytes(hidden)
            (exercise / "CMakeLists.txt").write_text(
                "cmake_minimum_required(VERSION 3.16)\n"
                f"project(multi_env_{ordinal} LANGUAGES CXX)\n"
                "set(CMAKE_CXX_STANDARD 17)\n"
                f"add_executable(multi_env_hidden {hidden_name})\n",
                encoding="utf-8",
            )
            rubric = AiderShadowRubric(
                task_id=exercise_name,
                split="train",
                editable_files=[str(value) for value in topic["editable_files"]],
                hidden_test_file=hidden_name,
                hidden_test_sha256=_sha256_bytes(hidden),
                source_prompt_sha256=_sha256_bytes(instructions),
                reference_answer_packaged=False,
                verification_stage="passed",
                verification_gate="strange-multi-env-gcc13.3-v1",
                family=slug,
                category="official-fixed26-policy-environment",
                lineage_id=f"polyglot-cpp/{slug}",
                episode_kind="policy-environment",
                objective_group=f"{slug}/{policy}",
                failure_signature=f"validated-strange-{slug}-{policy}",
                tags=[
                    "multi-env-strange-v1",
                    f"strange-topic:{slug}",
                    f"strange-policy:{policy}",
                    *("strange-terminal-policy" for _ in [0] if policy in terminal),
                ],
            )
            (exercise / ".rubric.json").write_text(
                rubric.model_dump_json(indent=2) + "\n", encoding="utf-8"
            )

    manifest = {
        "kind": SOURCE_MANIFEST_KIND,
        "schema_version": 1,
        "source_locator": f"polyglot-benchmark@{POLYGLOT_COMMIT}:cpp/exercises/practice",
        "counts": {"tasks": int(config["expected_train_count"])},
        "contract": {
            "official_task_id_overlap": overlap,
            "official_training_authorized": True,
            "reference_answers_packaged": False,
            "shared_hidden_tests_within_lineage": False,
            "model_prompt_contains_policy_text": False,
            "policy_environment_count": int(config["expected_train_count"]),
            "topic_count": int(config["expected_topic_count"]),
        },
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return output


def build_data(args: argparse.Namespace) -> dict[str, Path]:
    tasks_dir = Path(args.tasks_dir).resolve()
    if not tasks_dir.is_dir() or tasks_dir.is_symlink():
        raise ValueError("--tasks-dir must be a regular directory")
    with TemporaryDirectory(prefix="multi-env-strange-source-") as temporary:
        source = _write_task_source(Path(temporary))
        return build_aider_polyglot_datasets(
            source,
            args.out,
            train_limit=args.train_limit,
            monitor_limit=args.eval_limit or int(load_config()["expected_topic_count"]),
            profile=args.profile,
            run_id=args.run_id,
            sort_by_size=args.sort_by_size,
            force=args.force,
        )


def _copy_fixture(topic: dict[str, Any], destination: Path) -> None:
    source = _validate_fixture(topic)
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()):
        raise ValueError("fixture destination must be empty")
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if path.is_symlink():
            raise ValueError(f"fixture contains a symlink: {topic['slug']}/{relative}")
        if path.is_dir():
            (destination / relative).mkdir(exist_ok=True)
        elif path.is_file():
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def _sample_metadata(sample: Any) -> dict[str, Any]:
    value = sample.get("metadata") if isinstance(sample, dict) else getattr(sample, "metadata", None)
    return value if isinstance(value, dict) else {}


def _sample_response(sample: Any) -> str:
    value = sample.get("response") if isinstance(sample, dict) else getattr(sample, "response", "")
    return str(value or "")


def _sample_index(sample: Any) -> int | None:
    value = sample.get("index") if isinstance(sample, dict) else getattr(sample, "index", None)
    return value if isinstance(value, int) else None


def _resolve_task_path(value: str, metadata: dict[str, Any]) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    for root in (metadata.get("task_root"), os.environ.get("GLM47_DATA_DIR"), Path.cwd()):
        if root:
            candidate = Path(root) / path
            if candidate.exists():
                return candidate
    return Path.cwd() / path


def _tag_value(tags: list[str], prefix: str) -> str:
    matches = [tag[len(prefix) :] for tag in tags if tag.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"task must contain exactly one {prefix} tag")
    return matches[0]


def _docker_image() -> str:
    return os.environ.get("GLM47_MULTI_ENV_VERIFIER_IMAGE", str(load_config()["verifier_image"]))


def _docker_reward_root() -> Path:
    return Path(os.environ.get("GLM47_MULTI_ENV_REWARD_ROOT", str(REWARD_ROOT))).resolve()


def _verifier_timeout() -> int:
    try:
        return max(60, int(os.environ.get("GLM47_MULTI_ENV_VERIFIER_TIMEOUT_S", DEFAULT_TIMEOUT_SECONDS)))
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS


def _invoke_verifier(topic: str, policy: str, candidate: Path) -> dict[str, Any]:
    docker_reward_root = _docker_reward_root()
    for relative in (
        "multi_env_grpo_config.json",
        "multi_env_verifier_runner.py",
    ):
        path = docker_reward_root / relative
        if not path.is_file() or path.is_symlink():
            return {
                "status": "invalid",
                "infrastructure_error": f"nested-Docker reward root is missing {relative}",
            }
    with TemporaryDirectory(prefix="multi-env-strange-receipt-") as temporary:
        output = Path(temporary)
        candidate.chmod(0o755)
        output.chmod(0o777)
        container_candidate = f"/workspace/candidate/{topic}"
        command = [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--user",
            f"{os.getuid()}:{os.getgid()}",
            "--pids-limit",
            "2048",
            "--memory",
            "8g",
            "--tmpfs",
            "/tmp:rw,nosuid,nodev,size=2g",
            "--volume",
            f"{docker_reward_root}:/workspace/Reward_GRPO:ro",
            "--volume",
            f"{candidate}:{container_candidate}:ro",
            "--volume",
            f"{output}:/workspace/output:rw",
            "--env",
            "PYTHONDONTWRITEBYTECODE=1",
            _docker_image(),
            "python3",
            "/workspace/Reward_GRPO/multi_env_verifier_runner.py",
            "--config",
            "/workspace/Reward_GRPO/multi_env_grpo_config.json",
            "--reward-root",
            "/workspace/Reward_GRPO",
            "--candidate-dir",
            container_candidate,
            "--output-dir",
            "/workspace/output",
            "--topic",
            topic,
            "--policy",
            policy,
        ]
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=_verifier_timeout(),
            )
        except (OSError, subprocess.SubprocessError) as error:
            return {"status": "invalid", "infrastructure_error": str(error)}
        receipt_path = output / "multi_env_verification_receipt.json"
        if not receipt_path.is_file() or receipt_path.is_symlink():
            return {
                "status": "invalid",
                "infrastructure_error": "verifier container produced no aggregate receipt",
                "return_code": completed.returncode,
                "stderr": completed.stderr[-4000:],
            }
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            return {"status": "invalid", "infrastructure_error": str(error)}
        receipt["aggregate_receipt_sha256"] = _sha256_file(receipt_path)
        receipt["return_code"] = completed.returncode
        if completed.returncode not in {0, 1, 2}:
            receipt["status"] = "invalid"
            receipt["infrastructure_error"] = "unexpected verifier-container return code"
        return receipt


def _base_record(sample: Any, task: AiderPolyglotTask) -> dict[str, Any]:
    return {
        "task_id": task.task_id,
        "problem_id": task.exercise,
        "split": task.split,
        "sample_index": _sample_index(sample),
        "rollout_id": getattr(sample, "rollout_id", None),
        "response": _sample_response(sample),
        "verification_gate": task.verification_gate,
        "objective_group": task.objective_group,
    }


def _error_record(
    sample: Any,
    metadata: dict[str, Any],
    reason: str,
    *,
    infrastructure: bool,
    exception: str | None = None,
) -> dict[str, Any]:
    return {
        "score": 0.0 if infrastructure else -1.0,
        "reward": 0.0 if infrastructure else -1.0,
        "reason": reason,
        "task_id": metadata.get("task_id"),
        "problem_id": metadata.get("problem_id"),
        "split": metadata.get("split"),
        "sample_index": _sample_index(sample),
        "rollout_id": getattr(sample, "rollout_id", None),
        "response": _sample_response(sample),
        "format_valid": False,
        "modified_files": [],
        "tests_passed": 0,
        "tests_total": 0,
        "all_tests_pass": False,
        "infrastructure_error": infrastructure,
        **({"exception": exception} if exception else {}),
    }


def _project_reward(receipt: dict[str, Any], format_valid: bool) -> tuple[float, int, int]:
    results = receipt.get("policy_results")
    if not isinstance(results, list) or not results:
        raise ValueError("aggregate receipt has no policy results")
    policy_scores: list[float] = []
    passed = 0
    total = 0
    for result in results:
        if not isinstance(result, dict) or result.get("status") == "invalid":
            raise ValueError("aggregate receipt contains an invalid policy result")
        kernel_total = int(result.get("kernel_total") or 0)
        kernel_sum = result.get("kernel_sum")
        if kernel_total < 1 or not isinstance(kernel_sum, int):
            raise ValueError("aggregate receipt contains an invalid kernel denominator")
        policy_scores.append(kernel_sum / kernel_total)
        kernels = result.get("kernels") or []
        passed += sum(item.get("kernel") == 1 for item in kernels if isinstance(item, dict))
        total += sum(item.get("kernel") in {-1, 1} for item in kernels if isinstance(item, dict))
    diagnostic = sum(policy_scores) / len(policy_scores)
    reward = 1.0 if receipt.get("full_pass") is True else min(0.9, diagnostic)
    if not format_valid:
        reward -= 0.1
    return max(-1.0, min(1.0, reward)), passed, total


def _score_sample(sample: Any, *, reward_worker_load: int) -> dict[str, Any]:
    metadata = _sample_metadata(sample)
    task_path_value = metadata.get("task_path")
    if not task_path_value:
        return _error_record(sample, metadata, "missing_task_path", infrastructure=True)
    try:
        task_path = _resolve_task_path(str(task_path_value), metadata)
        task = AiderPolyglotTask.read_json(task_path)
        tags = [str(value) for value in task.tags]
        topic_slug = _tag_value(tags, "strange-topic:")
        policy = _tag_value(tags, "strange-policy:")
        topic = _topic_by_slug(topic_slug)
        if policy not in topic["live_policies"]:
            raise ValueError("task selects a non-live policy")
        parsed = parse_whole_file_response(_sample_response(sample), task.editable_files)
        for name, contents in parsed.files.items():
            _validate_candidate_source(name, contents)
        with TemporaryDirectory(prefix=f"multi-env-{topic_slug}-candidate-") as temporary:
            candidate = Path(temporary)
            _copy_fixture(topic, candidate)
            for name, contents in parsed.files.items():
                (candidate / name).write_text(contents, encoding="utf-8")
            receipt = _invoke_verifier(topic_slug, policy, candidate)
        if receipt.get("status") == "invalid":
            record = _base_record(sample, task)
            record.update(
                score=0.0,
                reward=0.0,
                reason="verifier_infrastructure_invalid",
                format_valid=parsed.format_valid,
                modified_files=sorted(parsed.files),
                tests_passed=0,
                tests_total=0,
                all_tests_pass=False,
                infrastructure_error=True,
                reward_worker_load=reward_worker_load,
                verifier_receipt=receipt,
            )
            return record
        reward, passed, total = _project_reward(receipt, parsed.format_valid)
        record = _base_record(sample, task)
        record.update(
            score=reward,
            reward=reward,
            reason="passed" if receipt.get("full_pass") else "policy_or_terminal_failure",
            format_valid=parsed.format_valid,
            modified_files=sorted(parsed.files),
            tests_passed=passed,
            tests_total=total,
            all_tests_pass=bool(receipt.get("full_pass")),
            terminal_pass=bool(receipt.get("terminal_pass")),
            infrastructure_error=False,
            reward_worker_load=reward_worker_load,
            reward_projection="equal-policy-bipolar-mean-terminal-full-pass-v1",
            selected_policy=policy,
            strange_topic=topic_slug,
            policy_results=receipt.get("policy_results"),
            verifier_receipt_sha256=receipt.get("aggregate_receipt_sha256"),
        )
        return record
    except AiderResponseError as error:
        return _error_record(sample, metadata, error.reason, infrastructure=False, exception=str(error))
    except CandidatePolicyError as error:
        return _error_record(
            sample, metadata, "forbidden_runtime_primitive", infrastructure=False, exception=str(error)
        )
    except Exception as error:  # pragma: no cover - protects remote rollout workers
        return _error_record(
            sample,
            metadata,
            "reward_exception",
            infrastructure=True,
            exception=f"{type(error).__name__}: {error}",
        )


@contextmanager
def _active_worker():
    global _ACTIVE_WORKERS
    with _ACTIVE_WORKERS_LOCK:
        _ACTIVE_WORKERS += 1
        worker_load = _ACTIVE_WORKERS
    try:
        yield worker_load
    finally:
        with _ACTIVE_WORKERS_LOCK:
            _ACTIVE_WORKERS -= 1


def _score_with_worker(sample: Any) -> dict[str, Any]:
    with _active_worker() as worker_load:
        return _score_sample(sample, reward_worker_load=worker_load)


def _reward_workers() -> int:
    try:
        return max(1, int(os.environ.get("GLM47_CPP_REWARD_WORKERS", DEFAULT_WORKERS)))
    except ValueError:
        return DEFAULT_WORKERS


async def reward_func(
    args: Any, sample: Any, **_kwargs: Any
) -> dict[str, Any] | list[dict[str, Any]]:
    """Miles custom-RM hook with group-neutral INVALID handling."""

    if isinstance(sample, list):
        semaphore = asyncio.Semaphore(max(1, min(len(sample), _reward_workers())))

        async def score(item: Any) -> dict[str, Any]:
            async with semaphore:
                return await asyncio.to_thread(_score_with_worker, item)

        records = list(await asyncio.gather(*(score(item) for item in sample)))
        return neutralize_infrastructure_scores(records)
    return await asyncio.to_thread(_score_with_worker, sample)


def build_verifier_image() -> None:
    image = _docker_image()
    completed = subprocess.run(
        ["docker", "build", "--file", str(DOCKERFILE_PATH), "--tag", image, str(REWARD_ROOT)],
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
    print(f"MULTI_ENV_VERIFIER_IMAGE_READY {image}")


def static_preflight() -> dict[str, Any]:
    config = load_config()
    for topic in config["topics"]:
        _validate_fixture(topic)
        _prompt_instructions(topic)
        for policy in topic["live_policies"]:
            _verifier_script(topic, str(policy))
    if not DOCKERFILE_PATH.is_file() or not RUNNER_PATH.is_file():
        raise RuntimeError("multi-environment verifier runtime files are missing")

    with TemporaryDirectory(prefix="multi-env-static-preflight-") as temporary:
        temporary_root = Path(temporary)
        source = _write_task_source(temporary_root / "source")
        output = temporary_root / "data"
        paths = build_aider_polyglot_datasets(
            source,
            output,
            monitor_limit=int(config["expected_topic_count"]),
            profile="multi-env-static-preflight",
            run_id="multi-env-static-preflight",
        )
        rows = [json.loads(line) for line in paths["grpo_train"].read_text(encoding="utf-8").splitlines()]
        if len(rows) != int(config["expected_train_count"]):
            raise RuntimeError("static preflight produced the wrong number of rows")
        prompts_by_topic: dict[str, set[str]] = {}
        for row in rows:
            tags = [str(value) for value in row["metadata"]["tags"]]
            topic = _tag_value(tags, "strange-topic:")
            prompt = json.dumps(row["prompt"], sort_keys=True, ensure_ascii=False)
            prompts_by_topic.setdefault(topic, set()).add(prompt)
        if any(len(prompts) != 1 for prompts in prompts_by_topic.values()):
            raise RuntimeError("policy metadata changed the model-facing prompt within a topic")
        manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
        receipt = {
            "schema_version": 1,
            "status": "passed",
            "polyglot_commit": POLYGLOT_COMMIT,
            "topic_count": len(config["topics"]),
            "policy_environment_count": len(rows),
            "monitor_count": manifest["counts"]["monitor"],
            "config_sha256": _sha256_file(CONFIG_PATH),
            "fixture_tree_sha256": _tree_sha256(FIXTURE_ROOT),
            "prompt_tree_sha256": _tree_sha256(PROMPT_ROOT),
            "source_tree_sha256": manifest["source_tree_sha256"],
            "model_prompt_policy_isolation": "passed",
        }
    print("MULTI_ENV_STRANGE_STATIC_PREFLIGHT_READY")
    return receipt


def preflight() -> None:
    receipt = static_preflight()
    run_response_contract_preflight()
    inspected = subprocess.run(
        ["docker", "image", "inspect", _docker_image()],
        check=False,
        capture_output=True,
        text=True,
    )
    if inspected.returncode != 0:
        raise RuntimeError(f"missing verifier image: {_docker_image()}")
    canaries: list[dict[str, Any]] = []
    for topic in load_config()["topics"]:
        with TemporaryDirectory(prefix=f"multi-env-{topic['slug']}-canary-") as temporary:
            candidate = Path(temporary)
            _copy_fixture(topic, candidate)
            for name in topic["editable_files"]:
                suffix = Path(str(name)).suffix
                example = candidate / ".meta" / f"example{suffix}"
                if example.is_file():
                    shutil.copy2(example, candidate / str(name))
            policy = _ordered_policies(topic)[0]
            result = _invoke_verifier(str(topic["slug"]), policy, candidate)
            if result.get("status") != "pass" or result.get("full_pass") is not True:
                raise RuntimeError(f"known-good canary failed for {topic['slug']}: {result}")
            canaries.append(
                {
                    "topic": topic["slug"],
                    "policy": policy,
                    "receipt_sha256": result["aggregate_receipt_sha256"],
                }
            )
    receipt["known_good_canaries"] = canaries
    receipt["verifier_image"] = _docker_image()
    receipt["status"] = "passed"
    output = REWARD_ROOT / "multi_env_grpo_preflight_receipt.json"
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("MULTI_ENV_STRANGE_REWARD_READY")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build-data")
    build.add_argument("--tasks-dir", required=True)
    build.add_argument("--out", required=True, type=Path)
    build.add_argument("--curriculum", choices=[CURRICULUM_NAME])
    build.add_argument("--train-limit", type=int)
    build.add_argument("--eval-limit", type=int)
    build.add_argument("--eval-splits", default="validation,test")
    build.add_argument("--profile", default="multi-env-strange-grpo20")
    build.add_argument("--run-id")
    build.add_argument("--sort-by-size", action="store_true")
    build.add_argument("--filter-train-oracle-full-marks", action="store_true")
    build.add_argument("--oracle-filter-workers", type=int, default=8)
    build.add_argument("--allow-non-gcc-curriculum", action="store_true")
    build.add_argument("--force", action="store_true")
    subparsers.add_parser("build-verifier-image")
    subparsers.add_parser("static-preflight")
    subparsers.add_parser("preflight")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    if args.command == "build-verifier-image":
        build_verifier_image()
        return
    if args.command == "static-preflight":
        print(json.dumps(static_preflight(), indent=2, sort_keys=True))
        return
    if args.command == "preflight":
        preflight()
        return
    if args.filter_train_oracle_full_marks:
        raise ValueError("the multi-environment curriculum is already verifier-bound")
    paths = build_data(args)
    print(json.dumps({key: str(value) for key, value in paths.items()}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
