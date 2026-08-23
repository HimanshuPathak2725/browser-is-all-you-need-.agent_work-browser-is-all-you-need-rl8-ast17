#include "allergies.h"

#include <array>
#include <string_view>

namespace allergies {
namespace {

std::array<std::pair<std::string_view, unsigned int>, 8> const& allergen_map() {
    static std::array<std::pair<std::string_view, unsigned int>, 8> const map{{
        std::pair<std::string_view, unsigned int>{"eggs", 1U},
        std::pair<std::string_view, unsigned int>{"peanuts", 2U},
        std::pair<std::string_view, unsigned int>{"shellfish", 4U},
        std::pair<std::string_view, unsigned int>{"strawberries", 8U},
        std::pair<std::string_view, unsigned int>{"tomatoes", 16U},
        std::pair<std::string_view, unsigned int>{"chocolate", 32U},
        std::pair<std::string_view, unsigned int>{"pollen", 64U},
        std::pair<std::string_view, unsigned int>{"cats", 128U}
    }};
    return map;
}

}  // namespace

allergy_test::allergy_test(unsigned int test_result) : score_(test_result) {}

bool allergy_test::is_allergic_to(std::string const& allergen) const {
    for (auto const& [item, score] : allergen_map()) {
        if (allergen == item) {
            return (score_ & score) != 0U;
        }
    }
    return false;
}

std::unordered_set<std::string> allergy_test::get_allergies() const {
    std::unordered_set<std::string> result;
    for (auto const& [item, score] : allergen_map()) {
        if ((score_ & score) != 0U) {
            result.emplace(item);
        }
    }
    return result;
}

}  // namespace allergies
