# Policy 5 verifier: isolate empty, singleton, and bounded small-input safety.
from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, execute
from strange_cpp_semantic import compile_and_run

from _contract import CONTRACT


POLICY_ID = "CS-E05"
PROBE = r'''#include "crypto_square.h"
#include <array>
#include <cctype>
#include <iostream>
#include <string>
#include <vector>

std::string normalize(const std::string& input) {
    std::string output;
    for (const unsigned char character : input) {
        if (std::isalnum(character)) output.push_back(static_cast<char>(std::tolower(character)));
    }
    return output;
}

std::size_t columns(std::size_t length) {
    std::size_t result = 0;
    while (result * result < length) ++result;
    return result;
}

std::vector<std::string> segments(const std::string& input) {
    const std::string normalized = normalize(input);
    const std::size_t width = columns(normalized.size());
    std::vector<std::string> rows;
    if (width == 0) return rows;
    for (std::size_t offset = 0; offset < normalized.size(); offset += width) {
        rows.push_back(normalized.substr(offset, width));
    }
    return rows;
}

int main(int argc, char** argv) {
    if (argc != 2) return 90;
    const std::string group(argv[1]);
    if (group == "empty_punctuation") {
        for (const std::string& input : {std::string(""), std::string("... --- ...")}) {
            const crypto_square::cipher value(input);
            if (!value.normalize_plain_text().empty() || value.size() != 0 ||
                !value.plain_text_segments().empty() || !value.cipher_text().empty() ||
                !value.normalized_cipher_text().empty()) return 1;
        }
    } else if (group == "singleton_one_row") {
        const crypto_square::cipher one("A");
        const crypto_square::cipher two("ab");
        if (one.normalize_plain_text() != "a" || one.size() != 1 ||
            one.plain_text_segments() != std::vector<std::string>{"a"} ||
            one.cipher_text() != "a" || one.normalized_cipher_text() != "a") return 2;
        if (two.normalize_plain_text() != "ab" || two.size() != 2 ||
            two.plain_text_segments() != std::vector<std::string>{"ab"} ||
            two.cipher_text() != "ab" || two.normalized_cipher_text() != "a b") return 3;
    } else if (group == "small_domain_sweep") {
        const std::array<std::string, 10> inputs{
            "", "!", "A", "ab", "a b c", "abcd", "abcde", "123456", "A1,b2!", "abcdefghi"};
        for (const auto& input : inputs) {
            const crypto_square::cipher value(input);
            const std::string normalized = normalize(input);
            if (value.normalize_plain_text() != normalized || value.size() != columns(normalized.size()) ||
                value.plain_text_segments() != segments(input) || value.cipher_text().size() != normalized.size() ||
                value.normalized_cipher_text().size() < value.cipher_text().size()) return 4;
        }
    } else return 91;
    std::cout << "ok:" << group << '\n';
}
'''


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_and_run(ctx, "CS-E05-A", "empty_punctuation", "safety_empty_punctuation.cpp", PROBE, "ok:empty_punctuation\n"),
        compile_and_run(ctx, "CS-E05-B", "singleton_one_row", "safety_singleton_one_row.cpp", PROBE, "ok:singleton_one_row\n"),
        compile_and_run(ctx, "CS-E05-C", "small_domain_sweep", "safety_small_domain_sweep.cpp", PROBE, "ok:small_domain_sweep\n"),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
