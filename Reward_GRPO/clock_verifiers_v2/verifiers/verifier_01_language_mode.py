from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_and_run, compile_only, execute

from _contract import CONTRACT
from _helpers import compile_implementation_only


POLICY_ID = "CL2-C01"
HEADER_PROBE = r'''#include "clock.h"
#if __cplusplus != 201703L
#error unexpected language mode
#endif
int main() { return 0; }
'''
CALLER_PROBE = r'''#include "clock.h"
#include <iostream>
#include <string>
int main() {
    const auto value = date_independent::clock::at(0, 0);
    const std::string rendered = static_cast<std::string>(value);
    if (rendered.empty()) return 1;
    std::cout << "language-ok\n";
}
'''


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_only(ctx, "CL2-C01-A", "cxx17_header", "cxx17_header.cpp", HEADER_PROBE),
        compile_implementation_only(ctx, "CL2-C01-B", "strict_implementation"),
        compile_and_run(ctx, "CL2-C01-C", "cxx17_public_caller", "cxx17_caller.cpp", CALLER_PROBE, "language-ok\n"),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
