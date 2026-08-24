from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_only, execute

from _contract import CONTRACT
from _helpers import compile_multi_tu_and_run


POLICY_ID = "CSF-C02"
EXACT_API = r'''#include "crypto_square.h"
#include <string>
#include <type_traits>
#include <vector>
using C = crypto_square::cipher;
using Normalize = std::string (C::*)() const;
using Size = std::size_t (C::*)() const;
using Segments = std::vector<std::string> (C::*)() const;
using Text = std::string (C::*)() const;
static_assert(std::is_constructible_v<C, const std::string&>);
static_assert(std::is_copy_constructible_v<C>);
static_assert(std::is_same_v<decltype(static_cast<Normalize>(&C::normalize_plain_text)), Normalize>);
static_assert(std::is_same_v<decltype(static_cast<Size>(&C::size)), Size>);
static_assert(std::is_same_v<decltype(static_cast<Segments>(&C::plain_text_segments)), Segments>);
static_assert(std::is_same_v<decltype(static_cast<Text>(&C::cipher_text)), Text>);
static_assert(std::is_same_v<decltype(static_cast<Text>(&C::normalized_cipher_text)), Text>);
int main() { return 0; }
'''
REPEATED_INCLUDE = '#include "crypto_square.h"\n#include "crypto_square.h"\nint main() { return 0; }\n'
HELPER = r'''#include "crypto_square.h"
#include <cstddef>
#include <string>
std::size_t observe_elsewhere(const crypto_square::cipher& value) {
    (void)value.normalize_plain_text();
    (void)value.plain_text_segments();
    (void)value.cipher_text();
    (void)value.normalized_cipher_text();
    return value.size();
}
'''
MAIN = r'''#include "crypto_square.h"
#include <cstddef>
#include <iostream>
std::size_t observe_elsewhere(const crypto_square::cipher&);
int main() {
    const crypto_square::cipher value("");
    if (observe_elsewhere(value) != 0) return 1;
    std::cout << "integration-ok\n";
}
'''


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_only(ctx, "CSF-C02-A", "exact_public_method_types", "exact_api.cpp", EXACT_API),
        compile_only(ctx, "CSF-C02-B", "idempotent_header_include", "repeated_include.cpp", REPEATED_INCLUDE),
        compile_multi_tu_and_run(
            ctx,
            "CSF-C02-C",
            "multi_tu_odr_surface",
            {"helper.cpp": HELPER, "main.cpp": MAIN},
            "integration-ok\n",
        ),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
