from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_and_run, execute

from _contract import CONTRACT


POLICY_ID = "DMF-C04"
GLYPH_AND_SPACING = r'''#include "diamond.h"
#include <algorithm>
#include <cstddef>
#include <iostream>
int main() {
    for (char letter = 'A'; letter <= 'Z'; ++letter) {
        const int n = letter - 'A';
        const std::size_t side = static_cast<std::size_t>(2 * n + 1);
        const auto actual = diamond::rows(letter);
        if (actual.size() != side) return 1;
        for (std::size_t row = 0; row < side; ++row) {
            if (actual.at(row).size() != side) return 2;
            const int signed_row = static_cast<int>(row);
            const int level = std::min(signed_row, 2 * n - signed_row);
            const int outer = n - level;
            const char glyph = static_cast<char>('A' + level);
            int glyph_count = 0;
            for (std::size_t column = 0; column < side; ++column) {
                const bool left = static_cast<int>(column) == outer;
                const bool right = level > 0 && static_cast<int>(column) == outer + 2 * level;
                const char expected = left || right ? glyph : ' ';
                if (actual.at(row).at(column) != expected) return 3;
                if (actual.at(row).at(column) != ' ') ++glyph_count;
            }
            if (glyph_count != (level == 0 ? 1 : 2)) return 4;
        }
    }
    std::cout << "geometry-ok\n";
}
'''
SYMMETRY_AND_ORDER = r'''#include "diamond.h"
#include <algorithm>
#include <cstddef>
#include <iostream>
#include <string>
int main() {
    for (char letter = 'A'; letter <= 'Z'; ++letter) {
        const int n = letter - 'A';
        const std::size_t side = static_cast<std::size_t>(2 * n + 1);
        const auto actual = diamond::rows(letter);
        if (actual.size() != side) return 1;
        for (std::size_t row = 0; row < side; ++row) {
            if (actual.at(row).size() != side) return 2;
            std::string reversed = actual.at(row);
            std::reverse(reversed.begin(), reversed.end());
            if (reversed != actual.at(row)) return 3;
            if (actual.at(row) != actual.at(side - 1 - row)) return 4;
            const int signed_row = static_cast<int>(row);
            const int level = std::min(signed_row, 2 * n - signed_row);
            const char glyph = static_cast<char>('A' + level);
            for (char byte : actual.at(row)) if (byte != ' ' && byte != glyph) return 5;
        }
        if (actual.at(static_cast<std::size_t>(n)).find(letter) == std::string::npos) return 6;
    }
    std::cout << "relations-ok\n";
}
'''


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_and_run(ctx, "DMF-C04-A", "glyph_and_spacing_relations", "geometry.cpp", GLYPH_AND_SPACING, "geometry-ok\n"),
        compile_and_run(ctx, "DMF-C04-B", "symmetry_and_order_relations", "relations.cpp", SYMMETRY_AND_ORDER, "relations-ok\n"),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
