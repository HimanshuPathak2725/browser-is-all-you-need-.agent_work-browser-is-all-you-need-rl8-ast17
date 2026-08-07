#pragma once

#include <array>
#include <string>
#include <string_view>
#include <vector>

namespace charm::allergy {

class SensitivityMask {
public:
    SensitivityMask(unsigned raw_mask, int rotation)
        : mask_(raw_mask & 0xffU), rotation_(normalize(rotation)) {}

    bool reacts_to(std::string_view allergen) const {
        for (std::size_t index = 0; index < names_.size(); ++index) {
            if (names_[index] == allergen) {
                const std::size_t bit = (index + static_cast<std::size_t>(rotation_)) % names_.size();
                return (mask_ & (1U << bit)) != 0U;
            }
        }
        return false;
    }

    std::vector<std::string> reactions() const {
        std::vector<std::string> result;
        for (std::string_view name : names_) {
            if (reacts_to(name)) {
                result.emplace_back(name);
            }
        }
        return result;
    }

private:
    static int normalize(int rotation) {
        const int remainder = rotation % 8;
        return remainder < 0 ? remainder + 8 : remainder;
    }

    inline static constexpr std::array<std::string_view, 8> names_{
        "cedar", "dust", "egg", "latex", "mold", "nickel", "pollen", "wool"};
    unsigned mask_;
    int rotation_;
};

}  // namespace charm::allergy
