#pragma once

#include <string>
#include <string_view>
#include <vector>

namespace charm::allergy {

class SensitivityMask {
public:
    SensitivityMask(unsigned raw_mask, int rotation)
        : mask_(raw_mask), rotation_(normalize_rotation(rotation)) {}

    bool reacts_to(std::string_view allergen) const;
    std::vector<std::string> reactions() const;

private:
    unsigned mask_;
    int rotation_;
};

}  // namespace charm::allergy
