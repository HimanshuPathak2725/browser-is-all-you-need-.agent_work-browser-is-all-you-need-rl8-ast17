#include "rotating-sensitivity-mask.hpp"

#include <cassert>
#include <string>
#include <vector>

using charm::allergy::SensitivityMask;

int main() {
    const SensitivityMask none(0U, 0);
    assert(none.reactions().empty() && !none.reacts_to("unknown"));

    const SensitivityMask basic(0b00000101U, 0);
    assert(basic.reacts_to("cedar") && basic.reacts_to("egg") && !basic.reacts_to("dust"));

    const SensitivityMask shifted(0b00000100U, 1);
    assert(shifted.reacts_to("dust") && !shifted.reacts_to("egg"));

    const SensitivityMask negative(0b10000000U, -1);
    assert(negative.reacts_to("cedar"));

    const SensitivityMask high_bits(0x100U | 0x02U, 8);
    assert((high_bits.reactions() == std::vector<std::string>{"dust"}));

    const SensitivityMask order(0xffU, 12345);
    assert((order.reactions() == std::vector<std::string>{
        "cedar", "dust", "egg", "latex", "mold", "nickel", "pollen", "wool"}));
    return 0;
}
