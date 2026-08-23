#include "allergies.h"

#include <cstddef>

namespace allergies {

allergy_test::allergy_test(unsigned int test_result) : score_(test_result) {}

bool allergy_test::is_allergic_to(std::string const& allergen) const {
    if (allergen == "eggs") {
        return (score_ & 1U) != 0U;
    }
    if (allergen == "peanuts") {
        return (score_ & 2U) != 0U;
    }
    if (allergen == "shellfish") {
        return (score_ & 4U) != 0U;
    }
    if (allergen == "strawberries") {
        return (score_ & 8U) != 0U;
    }
    if (allergen == "tomatoes") {
        return (score_ & 16U) != 0U;
    }
    if (allergen == "chocolate") {
        return (score_ & 32U) != 0U;
    }
    if (allergen == "pollen") {
        return (score_ & 64U) != 0U;
    }
    if (allergen == "cats") {
        return (score_ & 128U) != 0U;
    }
    return false;
}

std::unordered_set<std::string> allergy_test::get_allergies() const {
    std::unordered_set<std::string> result;
    if ((score_ & 1U) != 0U) {
        result.emplace("eggs");
    }
    if ((score_ & 2U) != 0U) {
        result.emplace("peanuts");
    }
    if ((score_ & 4U) != 0U) {
        result.emplace("shellfish");
    }
    if ((score_ & 8U) != 0U) {
        result.emplace("strawberries");
    }
    if ((score_ & 16U) != 0U) {
        result.emplace("tomatoes");
    }
    if ((score_ & 32U) != 0U) {
        result.emplace("chocolate");
    }
    if ((score_ & 64U) != 0U) {
        result.emplace("pollen");
    }
    if ((score_ & 128U) != 0U) {
        result.emplace("cats");
    }
    return result;
}

}  // namespace allergies
