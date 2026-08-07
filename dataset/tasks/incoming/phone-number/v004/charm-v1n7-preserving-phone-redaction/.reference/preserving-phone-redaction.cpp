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
struct RedactedPhone { std::string text; std::size_t masked_digits; };
std::optional<RedactedPhone> redact_phone_digits(std::string_view text, std::size_t visible_digits, char mask);
}

std::optional<charm::v1n7::phone_number::RedactedPhone> charm::v1n7::phone_number::redact_phone_digits(std::string_view text,std::size_t visible_digits,char mask){if(std::isdigit(static_cast<unsigned char>(mask)))return std::nullopt;std::size_t total=0;for(char c:text)if(std::isdigit(static_cast<unsigned char>(c)))++total;if(visible_digits>total)return std::nullopt;std::size_t hide=total-visible_digits,seen=0;std::string out(text);for(char& c:out)if(std::isdigit(static_cast<unsigned char>(c))){if(seen<hide)c=mask;++seen;}return RedactedPhone{std::move(out),hide};}
