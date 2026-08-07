#pragma once

#include <algorithm>
#include <array>
#include <climits>
#include <cstdlib>
#include <future>
#include <cmath>
#include <complex>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <functional>
#include <limits>
#include <map>
#include <memory>
#include <numeric>
#include <optional>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace charm::v1n7::phone_number {
class NormalizedPhone { public: NormalizedPhone(std::string national_digits, std::string extension_digits); const std::string& digits() const; const std::string& extension() const; private: std::string digits_; std::string extension_; };
std::optional<NormalizedPhone> parse_normalized_phone(std::string_view text);
}
