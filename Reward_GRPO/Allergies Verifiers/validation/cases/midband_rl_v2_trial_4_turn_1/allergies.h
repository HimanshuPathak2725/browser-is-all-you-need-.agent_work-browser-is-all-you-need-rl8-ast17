#pragma once

#include <string>
#include <unordered_set>

namespace allergies {

class allergy_test {
public:
    allergy_test(unsigned int test_result);
    bool is_allergic_to(std::string const& allergen) const;
    std::unordered_set<std::string> get_allergies() const;

private:
    unsigned int score_;
};

}  // namespace allergies
