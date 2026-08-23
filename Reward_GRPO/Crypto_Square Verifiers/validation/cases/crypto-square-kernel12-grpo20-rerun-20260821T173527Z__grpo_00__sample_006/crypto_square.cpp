#include "crypto_square.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <vector>

namespace crypto_square {

cipher::cipher(std::string const& text) : text_(text) {}

std::string cipher::normalize_plain_text() const {
    std::string normalized;
    normalized.reserve(text_.size());
    for (char c : text_) {
        if (std::isalnum(c)) {
            normalized += static_cast<char>(std::tolower(c));
        }
    }
    return normalized;
}

std::size_t cipher::size() const {
    std::size_t n = normalize_plain_text().size();
    return static_cast<std::size_t>(std::ceil(std::sqrt(n)));
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::vector<std::string> segments;
    std::string const& normalized = normalize_plain_text();
    std::size_t cols = size();
    for (std::size_t i = 0; i < normalized.size(); i += cols) {
        segments.push_back(normalized.substr(i, cols));
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string result;
    std::size_t cols = size();
    for (std::size_t col = 0; col < cols; ++col) {
        for (std::size_t row = 0; row < cols; ++row) {
            std::size_t index = row * cols + col;
            if (index < normalize_plain_text().size()) {
                result += normalize_plain_text()[index];
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string result;
    std::size_t cols = size();
    for (std::size_t col = 0; col < cols; ++col) {
        if (col != 0) {
            result += ' ';
        }
        for (std::size_t row = 0; row < cols; ++row) {
            std::size_t index = row * cols + col;
            if (index < normalize_plain_text().size()) {
                result += normalize_plain_text()[index];
            }
        }
    }
    return result;
}

}  // namespace crypto_square
