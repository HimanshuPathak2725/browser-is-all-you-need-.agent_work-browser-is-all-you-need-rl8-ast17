#include "crypto_square.h"

#include <cctype>
#include <cmath>
#include <vector>

namespace crypto_square {

cipher::cipher(std::string const& text) : text_(text) {
    normalized_ = normalize_plain_text();
}

std::string cipher::normalize_plain_text() const {
    std::string res;
    std::size_t n = text_.length();
    for (std::size_t i = 0; i < n; ++i) {
        if (std::isalnum(text_[i])) {
            res += std::tolower(text_[i]);
        }
    }
    return res;
}

std::size_t cipher::size() const {
    return normalized_.size();
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::vector<std::string> res;
    std::size_t n = normalized_.length();
    if (n == 0) return res;
    std::size_t columns = static_cast<std::size_t>(std::ceil(std::sqrt(n)));
    std::size_t rows = (n + columns - 1) / columns;

    for (std::size_t col = 0; col < columns; ++col) {
        std::string seg;
        for (std::size_t row = 0; row < rows; ++row) {
            if (col + row * columns < n) {
                seg += normalized_[col + row * columns];
            }
        }
        res.push_back(seg);
    }
    return res;
}

std::string cipher::cipher_text() const {
    std::string res;
    std::size_t n = normalized_.length();
    if (n == 0) return res;
    std::size_t columns = static_cast<std::size_t>(std::ceil(std::sqrt(n)));
    std::size_t rows = (n + columns - 1) / columns;

    for (std::size_t col = 0; col < columns; ++col) {
        for (std::size_t row = 0; row < rows; ++row) {
            if (col + row * columns < n) {
                res += normalized_[col + row * columns];
            }
        }
    }
    return res;
}

std::string cipher::normalized_cipher_text() const {
    std::string res;
    std::size_t n = normalized_.length();
    if (n == 0) return res;
    std::size_t columns = static_cast<std::size_t>(std::ceil(std::sqrt(n)));
    std::size_t rows = (n + columns - 1) / columns;

    for (std::size_t col = 0; col < columns; ++col) {
        for (std::size_t row = 0; row < rows; ++row) {
            if (col + row * columns < n) {
                res += normalized_[col + row * columns];
            } else {
                res += ' ';
            }
        }
        if (col < columns - 1) {
            res += ' ';
        }
    }
    return res;
}

}  // namespace crypto_square
