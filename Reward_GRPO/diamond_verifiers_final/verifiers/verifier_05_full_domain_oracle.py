from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_and_run, execute

from _contract import CONTRACT


POLICY_ID = "DMF-C05"
ORACLE_SUPPORT = r'''#include "diamond.h"
#include <algorithm>
#include <cstddef>
#include <iostream>
#include <string>
#include <vector>
std::vector<std::string> expected_rows(char letter) {
    const int n = letter - 'A';
    const int side = 2 * n + 1;
    std::vector<std::string> value;
    for (int row = 0; row < side; ++row) {
        const int level = std::min(row, 2 * n - row);
        const int outer = n - level;
        std::string line(static_cast<std::size_t>(side), ' ');
        line.at(static_cast<std::size_t>(outer)) = static_cast<char>('A' + level);
        if (level > 0) line.at(static_cast<std::size_t>(outer + 2 * level)) = static_cast<char>('A' + level);
        value.push_back(line);
    }
    return value;
}
'''
FULL_DOMAIN = ORACLE_SUPPORT + r'''
int main() {
    int checked = 0;
    for (char letter = 'A'; letter <= 'Z'; ++letter) {
        if (diamond::rows(letter) != expected_rows(letter)) return 1;
        ++checked;
    }
    std::cout << "oracle-ok " << checked << "\n";
}
'''
INTERLEAVED = ORACLE_SUPPORT + r'''
int main() {
    const std::vector<char> sequence{'Z', 'A', 'M', 'C', 'Y', 'B', 'E', 'D', 'Z', 'M'};
    for (int round = 0; round < 3; ++round) {
        for (char letter : sequence) {
            const auto expected = expected_rows(letter);
            const auto first = diamond::rows(letter);
            const auto second = diamond::rows(letter);
            if (first != expected || second != expected || first != second) return 1;
        }
    }
    for (char letter = 'Z'; letter >= 'A'; --letter) {
        if (diamond::rows(letter) != expected_rows(letter)) return 2;
    }
    std::cout << "repeat-ok\n";
}
'''
SAFETY_FLAGS = ("-O1", "-D_GLIBCXX_ASSERTIONS", "-fsanitize=undefined", "-fno-sanitize-recover=undefined")


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_and_run(
            ctx,
            "DMF-C05-A",
            "full_a_to_z_byte_oracle",
            "full_oracle.cpp",
            FULL_DOMAIN,
            "oracle-ok 26\n",
            extra_flags=SAFETY_FLAGS,
        ),
        compile_and_run(
            ctx,
            "DMF-C05-B",
            "interleaved_repeat_oracle",
            "repeat_oracle.cpp",
            INTERLEAVED,
            "repeat-ok\n",
            extra_flags=SAFETY_FLAGS,
        ),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
