from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_and_run, execute

from _contract import CONTRACT


POLICY_ID = "CSF-C04"
LENGTH_SWEEP = r'''#include "crypto_square.h"
#include <cstddef>
#include <iostream>
#include <string>
#include <vector>
std::size_t columns_for(std::size_t length) {
    std::size_t columns = 0;
    while (columns * columns < length) ++columns;
    return columns;
}
std::vector<std::string> expected_segments(const std::string& normalized) {
    std::vector<std::string> result;
    const std::size_t columns = columns_for(normalized.size());
    if (columns == 0) return result;
    for (std::size_t offset = 0; offset < normalized.size(); offset += columns) {
        result.push_back(normalized.substr(offset, columns));
    }
    return result;
}
int main() {
    const std::string alphabet = "abcdefghijklmnopqrstuvwxyz0123456789";
    for (std::size_t length = 0; length <= 1024; ++length) {
        std::string input;
        input.reserve(length);
        for (std::size_t index = 0; index < length; ++index) input.push_back(alphabet.at(index % alphabet.size()));
        const crypto_square::cipher value(input);
        const auto expected = expected_segments(input);
        if (value.plain_text_segments() != expected) return 1;
        if (value.plain_text_segments() != value.plain_text_segments()) return 2;
        if (!expected.empty()) {
            for (std::size_t row = 0; row + 1 < expected.size(); ++row) {
                if (expected.at(row).size() != value.size()) return 3;
            }
            if (expected.back().empty() || expected.back().size() > value.size()) return 4;
        }
    }
    std::cout << "segments-ok 1025\n";
}
'''
MIXED_SEGMENTS = r'''#include "crypto_square.h"
#include <iostream>
#include <string>
#include <utility>
#include <vector>
int main() {
    using Row = std::pair<std::string, std::vector<std::string>>;
    const std::vector<Row> cases{
        {"", {}},
        {"...", {}},
        {"A", {"a"}},
        {"A b", {"ab"}},
        {"This is fun!", {"thi", "sis", "fun"}},
        {"Chill out.", {"chi", "llo", "ut"}},
        {"1234 5678 90", {"1234", "5678", "90"}},
        {"A man, a plan, a canal: Panama!", {"amana", "plana", "canal", "panam", "a"}},
    };
    std::vector<std::vector<std::string>> saved;
    for (const auto& item : cases) {
        const crypto_square::cipher value(item.first);
        const auto first = value.plain_text_segments();
        const auto second = value.plain_text_segments();
        if (first != item.second || second != item.second) return 1;
        saved.push_back(first);
    }
    for (std::size_t index = cases.size(); index > 0; --index) {
        if (crypto_square::cipher(cases.at(index - 1).first).plain_text_segments() != saved.at(index - 1)) return 2;
    }
    std::cout << "mixed-segments-ok\n";
}
'''


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_and_run(ctx, "CSF-C04-A", "full_length_segment_sweep", "segments_sweep.cpp", LENGTH_SWEEP, "segments-ok 1025\n"),
        compile_and_run(ctx, "CSF-C04-B", "mixed_segment_and_repeat_relations", "mixed_segments.cpp", MIXED_SEGMENTS, "mixed-segments-ok\n"),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
