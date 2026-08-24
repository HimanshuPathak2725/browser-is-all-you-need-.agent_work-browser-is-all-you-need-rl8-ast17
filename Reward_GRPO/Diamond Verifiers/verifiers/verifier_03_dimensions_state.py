from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_and_run, execute

from _contract import CONTRACT


POLICY_ID = "DMF-C03"
DIMENSIONS = r'''#include "diamond.h"
#include <cstddef>
#include <iostream>
int main() {
    for (char letter = 'A'; letter <= 'Z'; ++letter) {
        const std::size_t side = static_cast<std::size_t>(2 * (letter - 'A') + 1);
        const auto value = diamond::rows(letter);
        if (value.size() != side) return 1;
        for (const auto& row : value) if (row.size() != side) return 2;
    }
    std::cout << "dimensions-ok\n";
}
'''
STATE_ISOLATION = r'''#include "diamond.h"
#include <iostream>
#include <string>
#include <vector>
int main() {
    const auto saved_m = diamond::rows('M');
    const auto first_z = diamond::rows('Z');
    if (diamond::rows('A') != std::vector<std::string>{"A"}) return 1;
    (void)diamond::rows('C');
    if (diamond::rows('M') != saved_m) return 2;
    if (diamond::rows('Z') != first_z) return 3;
    for (char letter = 'A'; letter <= 'Z'; ++letter) {
        const auto first = diamond::rows(letter);
        const auto second = diamond::rows(letter);
        if (first != second) return 4;
    }
    std::cout << "state-ok\n";
}
'''


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_and_run(ctx, "DMF-C03-A", "full_domain_dimensions", "dimensions.cpp", DIMENSIONS, "dimensions-ok\n"),
        compile_and_run(ctx, "DMF-C03-B", "repeat_and_state_isolation", "state.cpp", STATE_ISOLATION, "state-ok\n"),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
