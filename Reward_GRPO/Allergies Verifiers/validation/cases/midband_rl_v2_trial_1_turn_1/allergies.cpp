#include "allergies.h"

#include <array>
#include <cstddef>
#include <string_view>

namespace allergies {

allergy_test::allergy_test(unsigned int test_result) : result_(test_result) {}

bool allergy_test::is_allergic_to(std::string const& allergen) const {
    auto const found = allergen_to_bit_.find(allergen);
    if (found == allergen_to_bit_.end()) {
        return false;
    }
    return (result_ & found->second) != 0;
}

std::unordered_set<std::string> allergy_test::get_allergies() const {
    std::unordered_set<std::string> result;
    for (auto const& [allergen, bit] : allergen_to_bit_) {
        if ((result_ & bit) != 0) {
            result.emplace(allergen);
        }
    }
    return result;
}

std::unordered_map<std::string, unsigned int> const allergy_test::allergen_to_bit_{
    {"eggs", 1U},
    {"peanuts", 2U},
    {"shellfish", 4U},
    {"strawberries", 8U},
    {"tomatoes", 16U},
    {"chocolate", 32U},
    {"pollen", 64U},
    {"cats", 128U}
};

}  // namespace allergies
