#include "crypto_square.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <sstream>
#include <vector>

namespace crypto_square {

cipher::cipher(std::string const& text) : text_(text) {}

std::string cipher::normalize_plain_text() const {
    std::string result;
    result.reserve(text_.size());
    for (const auto& character : text_) {
        if (std::isalnum(character)) {
            result += std::tolower(character);
        }
    }
    return result;
}

std::size_t cipher::size() const {
    std::string normalized = normalize_plain_text();
    std::size_t n = normalized.size();
    std::size_t s = static_cast<std::size_t>(std::ceil(std::sqrt(n)));
    if (s > 1 && s * (s - 1) >= n) {
        return s - 1;
    }
    return s;
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::string normalized = normalize_plain_text();
    std::size_t s = size();
    std::vector<std::string> segments;
    segments.reserve(s);
    for (std::size_t row = 0; row < s; ++row) {
        std::size_t start = row * s;
        std::size_t length = s;
        segments.push_back(normalized.substr(start, length));
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string normalized = normalize_plain_text();
    std::size_t s = size();
    std::string result;
    result.reserve(normalized.size());
    for (std::size_t col = 0; col < s; ++col) {
        for (std::size_t row = 0; row < s; ++row) {
            result += normalized[row * s + col];
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string normalized = normalize_plain_text();
    std::size_t s = size();
    std::string result;
    result.reserve(normalized.size());
    for (std::size_t col = 0; col < s; ++col) {
        for (std::size_t row = 0; row < s; ++row) {
            if (row * s + col < normalized.size()) {
                result += normalized[row * s + col];
            } else {
                result += ' ';
            }
        }
        result += ' ';
    }
    return result;
}

}  // namespace crypto_square
