#pragma once
#include <cctype>
#include <optional>
#include <string>
#include <string_view>
namespace charm::phone {
struct CanonicalPhone { std::string number; std::string extension; };
inline std::optional<CanonicalPhone> canonicalize(std::string_view input) {
    std::string main_part(input);
    std::string extension;
    std::size_t marker = std::string::npos;
    for (std::size_t i = 0; i < main_part.size(); ++i) {
        if (main_part[i] == 'x' || main_part[i] == 'X') { marker = i; break; }
        if (i + 3 <= main_part.size()) {
            std::string token = main_part.substr(i, 3);
            for (char& ch : token) ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
            if (token == "ext") { marker = i; break; }
        }
    }
    if (marker != std::string::npos) {
        std::string tail = main_part.substr(marker);
        const std::size_t digit = tail.find_first_of("0123456789");
        if (digit == std::string::npos) return std::nullopt;
        for (std::size_t i = digit; i < tail.size(); ++i) {
            const unsigned char ch = tail[i];
            if (std::isdigit(ch)) extension.push_back(static_cast<char>(ch));
            else if (!std::isspace(ch) && ch != '.' && ch != '-') return std::nullopt;
        }
        if (extension.empty() || extension.size() > 6) return std::nullopt;
        main_part.resize(marker);
    }
    std::string digits;
    for (unsigned char ch : main_part) {
        if (std::isdigit(ch)) digits.push_back(static_cast<char>(ch));
        else if (std::isalpha(ch)) return std::nullopt;
        else if (!std::isspace(ch) && ch != '+' && ch != '-' && ch != '(' && ch != ')' && ch != '.') return std::nullopt;
    }
    if (digits.size() == 11 && digits.front() == '1') digits.erase(digits.begin());
    if (digits.size() != 10 || digits[0] < '2' || digits[0] > '9' || digits[3] < '2' || digits[3] > '9') return std::nullopt;
    return CanonicalPhone{digits, extension};
}
}
