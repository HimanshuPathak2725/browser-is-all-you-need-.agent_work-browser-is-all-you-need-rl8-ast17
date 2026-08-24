from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_and_run, execute

from _contract import CONTRACT


POLICY_ID = "CSF-C03"
NORMALIZATION = r'''#include "crypto_square.h"
#include <iostream>
#include <string>
#include <utility>
#include <vector>
int main() {
    const std::vector<std::pair<std::string, std::string>> cases{
        {"", ""},
        {"... --- ...", ""},
        {"A", "a"},
        {"  b ", "b"},
        {"@1,%!", "1"},
        {"A1, b2!", "a1b2"},
        {"A man, a plan, a canal: Panama!", "amanaplanacanalpanama"},
        {"Mixed CASE 0123456789", "mixedcase0123456789"},
        {"tabs\tand\nlines\r", "tabsandlines"},
        {"[]{}()_+-=/\\|;:'\"<>?`~", ""},
    };
    for (const auto& item : cases) {
        std::string source = item.first;
        const crypto_square::cipher value(source);
        source.assign("mutated after construction");
        for (int repeat = 0; repeat < 5; ++repeat) {
            if (value.normalize_plain_text() != item.second) return 1;
        }
    }
    std::cout << "normalization-ok " << cases.size() << "\n";
}
'''
SIZE_SWEEP = r'''#include "crypto_square.h"
#include <cstddef>
#include <iostream>
#include <string>
std::size_t expected_columns(std::size_t length) {
    std::size_t columns = 0;
    while (columns * columns < length) ++columns;
    return columns;
}
int main() {
    for (std::size_t length = 0; length <= 4096; ++length) {
        const crypto_square::cipher value(std::string(length, 'a'));
        const std::size_t columns = expected_columns(length);
        if (value.size() != columns) return 1;
        if (length == 0) continue;
        const std::size_t rows = (length + columns - 1) / columns;
        if (columns < rows || columns - rows > 1 || columns * rows < length) return 2;
    }
    if (crypto_square::cipher("A ! b ? C").size() != 2) return 3;
    if (crypto_square::cipher("1234 ---- 56789").size() != 3) return 4;
    std::cout << "size-ok 4097\n";
}
'''


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_and_run(ctx, "CSF-C03-A", "ascii_normalization_and_source_isolation", "normalization.cpp", NORMALIZATION, "normalization-ok 10\n"),
        compile_and_run(ctx, "CSF-C03-B", "full_length_size_sweep", "size_sweep.cpp", SIZE_SWEEP, "size-ok 4097\n"),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
