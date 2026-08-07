#pragma once
#include <cctype>
#include <optional>
#include <string>
#include <string_view>
namespace charm::phone {
inline std::optional<std::string> normalize_vanity(std::string_view input) {
    std::string digits;
    bool leading_plus = false;
    for (std::size_t index = 0; index < input.size(); ++index) {
        const unsigned char raw = input[index];
        if (raw == '+') { if (index != 0 || leading_plus) return std::nullopt; leading_plus = true; continue; }
        if (std::isdigit(raw)) { digits.push_back(static_cast<char>(raw)); continue; }
        if (std::isalpha(raw)) {
            const char ch = static_cast<char>(std::toupper(raw));
            const char mapped = ch <= 'C' ? '2' : ch <= 'F' ? '3' : ch <= 'I' ? '4' : ch <= 'L' ? '5' : ch <= 'O' ? '6' : ch <= 'S' ? '7' : ch <= 'V' ? '8' : '9';
            digits.push_back(mapped);
            continue;
        }
        if (!std::isspace(raw) && raw != '-' && raw != '(' && raw != ')' && raw != '.') return std::nullopt;
    }
    if (digits.size() != 10 && digits.size() != 11) return std::nullopt;
    if (leading_plus && digits.size() != 11) return std::nullopt;
    return (leading_plus ? "+" : "") + digits;
}
}
