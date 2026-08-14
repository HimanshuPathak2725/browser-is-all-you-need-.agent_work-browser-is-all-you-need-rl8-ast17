#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace charm::v1r87_37414::yacht {

std::optional<std::int64_t> evaluate_postfix_dice_rule(const std::vector<int>& dice, const std::vector<std::string>& program);
}
