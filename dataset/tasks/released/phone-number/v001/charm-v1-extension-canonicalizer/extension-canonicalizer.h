#pragma once
#include <optional>
#include <string>
#include <string_view>
namespace charm::phone {
struct CanonicalPhone { std::string number; std::string extension; };
std::optional<CanonicalPhone> canonicalize(string_view input);
}
