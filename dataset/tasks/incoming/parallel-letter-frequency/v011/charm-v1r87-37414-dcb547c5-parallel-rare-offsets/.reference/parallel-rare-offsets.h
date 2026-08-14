#pragma once

#include <cstddef>
#include <optional>
#include <string>
#include <vector>

namespace charm::v1r87_37414::parallel_letter_frequency {

std::optional<std::vector<std::size_t>> parallel_rare_letter_offsets(const std::vector<std::string>& lines, std::size_t workers);
}
