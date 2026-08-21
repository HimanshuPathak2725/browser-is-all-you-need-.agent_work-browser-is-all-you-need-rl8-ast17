"""Crypto Square GRPO curriculum and Strange-kernel reward adapter.

This module is intentionally outside the shared trainer and infrastructure
layers.  It builds eight answer-free Crypto Square episodes and delegates
candidate execution to the existing isolated Aider C++ sandbox.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Sequence

from glm47_posttraining.aider_polyglot.dataset import (
    SOURCE_MANIFEST_KIND,
    build_aider_polyglot_datasets,
)
from glm47_posttraining.aider_polyglot.harness import run_sandbox_preflight
from glm47_posttraining.aider_polyglot.schema import AiderShadowRubric
from glm47_posttraining.integrations.miles_aider_polyglot import (
    neutralize_infrastructure_scores,
)
from glm47_posttraining.integrations.miles_aider_polyglot import (
    reward_func as aider_reward_func,
)
from glm47_posttraining.integrations.miles_aider_polyglot import (
    run_response_contract_preflight,
)


CURRICULUM_NAME = "crypto-square-v1"
DATASET_KIND = "aider-polyglot-cpp-shadow-grpo"
POLYGLOT_COMMIT = "7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f"
VERIFICATION_GATE = "crypto-square-strange-12-kernel-gcc13-v1"
EDITABLE_FILES = ["crypto_square.h", "crypto_square.cpp"]
HIDDEN_TEST = "crypto_square_hidden_test.cpp"
KERNEL_COUNT = 12
POLICY_IDS = ["CS-E01", "CS-E02", "CS-E03", "CS-E04"]


INSTRUCTIONS = r"""# Crypto Square

Implement the classic square-code cipher. Normalize the input by retaining
letters and digits only and converting letters to lowercase. Arrange the
normalized text into the smallest rectangle whose column count is at least its
row count and differs by no more than one. Read the rectangle down its columns.

The public C++17 interface is exact:

```cpp
namespace crypto_square {
class cipher {
public:
    cipher(std::string const& text);
    std::string normalize_plain_text() const;
    std::size_t size() const;
    std::vector<std::string> plain_text_segments() const;
    std::string cipher_text() const;
    std::string normalized_cipher_text() const;
};
}
```

`cipher_text()` contains no separator or padding spaces. The normalized cipher
contains one space between chunks and preserves the trailing padding needed to
form a perfect rectangle. For example, `This is fun!` becomes
`tsf hiu isn`, while `Chill out.` becomes `clu hlt io `.

Only `crypto_square.h` and `crypto_square.cpp` are editable. The build uses
C++17 with `-Wall -Wextra -Wpedantic -Werror`. Do not modify or attempt to
inspect the hidden verifier.
"""


EXACT_HEADER = r"""#pragma once

#include <cstddef>
#include <string>
#include <vector>

namespace crypto_square {

class cipher {
public:
    explicit cipher(std::string const& text);
    std::string normalize_plain_text() const;
    std::size_t size() const;
    std::vector<std::string> plain_text_segments() const;
    std::string cipher_text() const;
    std::string normalized_cipher_text() const;

private:
    std::string text_;
};

}  // namespace crypto_square
"""


EMPTY_HEADER = r"""#pragma once

namespace crypto_square {
}
"""


EMPTY_SOURCE = r"""#include "crypto_square.h"

namespace crypto_square {
}
"""


MISSING_DEFINITIONS_SOURCE = EMPTY_SOURCE


PLAINTEXT_SOURCE = r"""#include "crypto_square.h"

#include <algorithm>
#include <cctype>
#include <cmath>

namespace crypto_square {

cipher::cipher(std::string const& text) : text_(text) {}

std::string cipher::normalize_plain_text() const { return text_; }

std::size_t cipher::size() const {
    return static_cast<std::size_t>(std::ceil(std::sqrt(text_.size())));
}

std::vector<std::string> cipher::plain_text_segments() const { return {text_}; }

std::string cipher::cipher_text() const { return text_; }

std::string cipher::normalized_cipher_text() const { return text_; }

}  // namespace crypto_square
"""


NORMALIZED_SOURCE = r"""#include "crypto_square.h"

#include <algorithm>
#include <cctype>
#include <cmath>

namespace crypto_square {

cipher::cipher(std::string const& text) {
    for (unsigned char character : text) {
        if (std::isalnum(character)) {
            text_.push_back(static_cast<char>(std::tolower(character)));
        }
    }
}

std::string cipher::normalize_plain_text() const { return text_; }

std::size_t cipher::size() const {
    return static_cast<std::size_t>(std::sqrt(text_.size()));
}

std::vector<std::string> cipher::plain_text_segments() const { return {text_}; }

std::string cipher::cipher_text() const { return text_; }

std::string cipher::normalized_cipher_text() const { return text_; }

}  // namespace crypto_square
"""


SEGMENT_SOURCE = r"""#include "crypto_square.h"

#include <cctype>

namespace crypto_square {

cipher::cipher(std::string const& text) {
    for (unsigned char character : text) {
        if (std::isalnum(character)) {
            text_.push_back(static_cast<char>(std::tolower(character)));
        }
    }
}

std::string cipher::normalize_plain_text() const { return text_; }

std::size_t cipher::size() const {
    std::size_t columns = 0;
    while (columns * columns < text_.size()) ++columns;
    return columns;
}

std::vector<std::string> cipher::plain_text_segments() const { return {text_}; }

std::string cipher::cipher_text() const { return text_; }

std::string cipher::normalized_cipher_text() const { return text_; }

}  // namespace crypto_square
"""


UNSPACED_SOURCE = r"""#include "crypto_square.h"

#include <cctype>

namespace crypto_square {

cipher::cipher(std::string const& text) {
    for (unsigned char character : text) {
        if (std::isalnum(character)) {
            text_.push_back(static_cast<char>(std::tolower(character)));
        }
    }
}

std::string cipher::normalize_plain_text() const { return text_; }

std::size_t cipher::size() const {
    std::size_t columns = 0;
    while (columns * columns < text_.size()) ++columns;
    return columns;
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::vector<std::string> rows;
    const std::size_t columns = size();
    if (columns == 0) return rows;
    for (std::size_t offset = 0; offset < text_.size(); offset += columns) {
        rows.push_back(text_.substr(offset, columns));
    }
    return rows;
}

std::string cipher::cipher_text() const {
    std::string output;
    const auto rows = plain_text_segments();
    for (std::size_t column = 0; column < size(); ++column) {
        for (const auto& row : rows) {
            if (column < row.size()) output.push_back(row[column]);
        }
    }
    return output;
}

std::string cipher::normalized_cipher_text() const { return cipher_text(); }

}  // namespace crypto_square
"""


HIDDEN_TEST_SOURCE = r"""#include "crypto_square.h"

#include <string>
#include <type_traits>
#include <utility>
#include <vector>

using Cipher = crypto_square::cipher;

static_assert(std::is_constructible_v<Cipher, const std::string&>);
static_assert(std::is_same_v<decltype(std::declval<const Cipher&>().normalize_plain_text()), std::string>);
static_assert(std::is_same_v<decltype(std::declval<const Cipher&>().size()), std::size_t>);
static_assert(std::is_same_v<decltype(std::declval<const Cipher&>().plain_text_segments()), std::vector<std::string>>);
static_assert(std::is_same_v<decltype(std::declval<const Cipher&>().cipher_text()), std::string>);
static_assert(std::is_same_v<decltype(std::declval<const Cipher&>().normalized_cipher_text()), std::string>);

int main() {
    if (Cipher("").normalize_plain_text() != "") return 1;
    if (Cipher("... --- ...").normalize_plain_text() != "") return 2;
    if (Cipher(" A1, b2! ").normalize_plain_text() != "a1b2") return 3;
    if (Cipher("").size() != 0) return 4;
    if (Cipher("ab").size() != 2 || Cipher("123456789").size() != 3 || Cipher("1234567890").size() != 4) return 5;
    if (Cipher("This is fun!").plain_text_segments() != std::vector<std::string>{"thi", "sis", "fun"}) return 6;
    if (Cipher("Chill out.").plain_text_segments() != std::vector<std::string>{"chi", "llo", "ut"}) return 7;
    if (Cipher("This is fun!").cipher_text() != "tsfhiuisn") return 8;
    if (Cipher("This is fun!").normalized_cipher_text() != "tsf hiu isn") return 9;
    if (Cipher("Chill out.").cipher_text() != "cluhltio") return 10;
    if (Cipher("Chill out.").normalized_cipher_text() != "clu hlt io ") return 11;
    if (Cipher("If man was meant to stay on the ground, god would have given us roots.").normalized_cipher_text() !=
        "imtgdvs fearwer mayoogo anouuio ntnnlvt wttddes aohghn  sseoau ") return 12;
    return 0;
}
"""


EPISODES = (
    ("full-solve", "missing-public-cipher-api", EMPTY_HEADER, EMPTY_SOURCE, ""),
    ("missing-definitions-repair", "declared-methods-not-defined", EXACT_HEADER, MISSING_DEFINITIONS_SOURCE, "The linker reports unresolved cipher method definitions."),
    ("normalization-repair", "normalization-and-lowercase", EXACT_HEADER, PLAINTEXT_SOURCE, "Punctuation, spaces, and uppercase letters remain in the normalized text."),
    ("square-size-repair", "ceil-square-dimensions", EXACT_HEADER, NORMALIZED_SOURCE, "The size calculation rounds down for incomplete squares."),
    ("segment-repair", "row-segmentation", EXACT_HEADER, SEGMENT_SOURCE, "The implementation returns one row instead of fixed-width plaintext segments."),
    ("transpose-repair", "column-transposition", EXACT_HEADER, SEGMENT_SOURCE, "The cipher output still follows plaintext order instead of reading columns."),
    ("spacing-padding-repair", "normalized-spacing-padding", EXACT_HEADER, UNSPACED_SOURCE, "The unspaced cipher is correct, but normalized output omits grouping and trailing padding."),
    ("eval-feedback-repair", "observed-midbreak-layout-failure", EXACT_HEADER, PLAINTEXT_SOURCE, "Observed evaluation failure: expected `clu hlt io ` but the candidate returned `chillout`."),
)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write_task_root(root: Path) -> Path:
    practice = root / "cpp" / "exercises" / "practice"
    hidden_hash = _sha256_text(HIDDEN_TEST_SOURCE)
    task_ids: list[str] = []
    for episode_kind, signature, header, source, feedback in EPISODES:
        task_id = f"crypto-square--{episode_kind}"
        task_ids.append(task_id)
        exercise = practice / task_id
        docs = exercise / ".docs"
        docs.mkdir(parents=True)
        task_instructions = INSTRUCTIONS
        if feedback:
            task_instructions += f"\n\n## Executed failure evidence\n\n{feedback}\n"
        (docs / "instructions.md").write_text(task_instructions, encoding="utf-8")
        (exercise / "crypto_square.h").write_text(header, encoding="utf-8")
        (exercise / "crypto_square.cpp").write_text(source, encoding="utf-8")
        (exercise / HIDDEN_TEST).write_text(HIDDEN_TEST_SOURCE, encoding="utf-8")
        (exercise / "CMakeLists.txt").write_text(
            "cmake_minimum_required(VERSION 3.16)\nproject(crypto_square LANGUAGES CXX)\n",
            encoding="utf-8",
        )
        rubric = AiderShadowRubric(
            task_id=task_id,
            split="train",
            editable_files=EDITABLE_FILES,
            hidden_test_file=HIDDEN_TEST,
            hidden_test_sha256=hidden_hash,
            source_prompt_sha256=_sha256_text(task_instructions),
            reference_answer_packaged=False,
            verification_stage="passed",
            verification_gate=VERIFICATION_GATE,
            family="crypto-square",
            category="crypto-square-strange",
            lineage_id="fixed26/crypto-square",
            episode_kind=episode_kind,
            objective_group="crypto-square-strange",
            failure_signature=signature,
            tags=[
                "official-task-training-authorized",
                "whole-file-action",
                "strange-kernel-reward",
                *POLICY_IDS,
            ],
        )
        (exercise / ".rubric.json").write_text(
            rubric.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
    manifest = {
        "kind": SOURCE_MANIFEST_KIND,
        "schema_version": 1,
        "source_locator": f"official:Aider-AI/polyglot-benchmark@{POLYGLOT_COMMIT}/crypto-square",
        "counts": {"tasks": len(task_ids), "train": len(task_ids), "validation": 0},
        "task_ids": task_ids,
        "contract": {
            "official_task_id_overlap": ["crypto-square"],
            "official_training_authorized": True,
            "reference_answers_packaged": False,
            "shared_hidden_tests_within_lineage": True,
            "verifier_policy_ids": POLICY_IDS,
            "kernel_count": KERNEL_COUNT,
        },
    }
    (root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return root


def build_data(args: argparse.Namespace) -> dict[str, Path]:
    if args.curriculum not in (None, CURRICULUM_NAME):
        raise ValueError(f"unsupported curriculum: {args.curriculum}")
    with TemporaryDirectory(prefix="crypto-square-strange-tasks-") as temporary:
        task_root = _write_task_root(Path(temporary))
        return build_aider_polyglot_datasets(
            task_root,
            args.out,
            train_limit=args.train_limit,
            monitor_limit=args.eval_limit or len(EPISODES),
            profile=args.profile,
            run_id=args.run_id,
            sort_by_size=args.sort_by_size,
            force=args.force,
        )


def _apply_kernel_reward(record: dict[str, Any]) -> dict[str, Any]:
    record["verifier_pack"] = "crypto-square-strange-v1"
    record["verifier_policy_ids"] = POLICY_IDS
    record["verification_gate"] = VERIFICATION_GATE
    if record.get("infrastructure_error"):
        record["kernel_sum"] = None
        record["kernel_total"] = KERNEL_COUNT
        record["kernel_status"] = "invalid"
        record["reward"] = 0.0
        record["score"] = 0.0
        return record
    passed = KERNEL_COUNT if record.get("all_tests_pass") else int(record.get("tests_passed") or 0)
    passed = max(0, min(KERNEL_COUNT, passed))
    failed = KERNEL_COUNT - passed
    kernel_sum = passed - failed
    record["kernel_passed"] = passed
    record["kernel_failed"] = failed
    record["kernel_sum"] = kernel_sum
    record["kernel_total"] = KERNEL_COUNT
    record["kernel_status"] = "pass" if passed == KERNEL_COUNT else "fail"
    record["reward"] = kernel_sum / KERNEL_COUNT
    record["score"] = record["reward"]
    return record


async def reward_func(
    args: Any, sample: Any, **kwargs: Any
) -> dict[str, Any] | list[dict[str, Any]]:
    result = await aider_reward_func(args, sample, **kwargs)
    if isinstance(result, list):
        records = [_apply_kernel_reward(record) for record in result]
        return neutralize_infrastructure_scores(records)
    return _apply_kernel_reward(result)


def preflight() -> None:
    run_response_contract_preflight()
    run_sandbox_preflight()
    with TemporaryDirectory(prefix="crypto-square-strange-preflight-") as temporary:
        root = Path(temporary)
        args = argparse.Namespace(
            curriculum=CURRICULUM_NAME,
            out=root / "data",
            train_limit=None,
            eval_limit=None,
            profile="crypto-square-preflight",
            run_id="crypto-square-preflight",
            sort_by_size=False,
            force=True,
        )
        paths = build_data(args)
        manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
        if manifest.get("kind") != DATASET_KIND or manifest["counts"]["train"] != len(EPISODES):
            raise RuntimeError("Crypto Square dataset preflight produced an invalid manifest")
    print("CRYPTO_SQUARE_STRANGE_REWARD_READY")


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
    build.add_argument("--profile", default="crypto-square-strange-grpo")
    build.add_argument("--run-id")
    build.add_argument("--sort-by-size", action="store_true")
    build.add_argument("--filter-train-oracle-full-marks", action="store_true")
    build.add_argument("--oracle-filter-workers", type=int, default=8)
    build.add_argument("--allow-non-gcc-curriculum", action="store_true")
    build.add_argument("--force", action="store_true")
    subparsers.add_parser("preflight")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    if args.command == "preflight":
        preflight()
        return
    if args.filter_train_oracle_full_marks:
        raise ValueError("the Crypto Square curriculum is already verifier-bound")
    paths = build_data(args)
    print(json.dumps({key: str(value) for key, value in paths.items()}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
