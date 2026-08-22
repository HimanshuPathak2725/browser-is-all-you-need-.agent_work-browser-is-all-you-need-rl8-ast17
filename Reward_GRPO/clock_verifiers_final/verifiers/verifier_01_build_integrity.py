from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_and_run, compile_only, execute

from _contract import CONTRACT
from _helpers import compile_implementation_only


POLICY_ID = "CLF-C01"
HEADER_PROBE = r'''#include "clock.h"
#if __cplusplus != 201703L
#error Clock verifier requires exact C++17 mode
#endif
int main() { return 0; }
'''
LINK_PROBE = r'''#include "clock.h"
#include <iostream>
#include <string>
int main() {
    auto value = date_independent::clock::at(24, -1);
    value.plus(1).minus(1);
    const std::string rendered = static_cast<std::string>(value);
    if (rendered.empty()) return 1;
    std::cout << "build-ok\n";
}
'''


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_only(ctx, "CLF-C01-A", "self_contained_cxx17_header", "header_first.cpp", HEADER_PROBE),
        compile_implementation_only(ctx, "CLF-C01-B", "strict_warning_clean_implementation"),
        compile_and_run(ctx, "CLF-C01-C", "external_compile_link", "external_link.cpp", LINK_PROBE, "build-ok\n"),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
