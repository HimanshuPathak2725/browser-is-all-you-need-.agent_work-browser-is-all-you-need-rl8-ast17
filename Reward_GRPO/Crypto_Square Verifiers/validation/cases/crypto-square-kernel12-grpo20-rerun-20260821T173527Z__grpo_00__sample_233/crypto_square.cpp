#include "crypto_square.h"

#include <algorithm>
#include <cmath>
#include <vector>

namespace crypto_square {

cipher::cipher(std::string const& text) {
    // Normalize: retain letters and digits, convert to lowercase
    std::string normalized;
    std::transform(text.begin(), text.end(), std::back_inserter(normalized),
                   [](unsigned char c) { return std::tolower(c); });
    normalized.erase(
        std::remove_if(normalized.begin(), normalized.end(),
                       [](unsigned char c) { return !std::isalnum(c); }),
        normalized.end());
    normalized_ = std::move(normalized);

    // Calculate dimensions: smallest rectangle with cols >= rows, diff <= 1
    if (normalized_.empty()) {
        cols_ = rows_ = 0;
    } else {
        cols_ = static_cast<std::size_t>(std::ceil(std::sqrt(normalized_.size())));
        rows_ = static_cast<std::size_t>(std::ceil(normalized_.size() / static_cast<double>(cols_)));
    }
}

std::string cipher::normalize_plain_text() const {
    return normalized_;
}

std::size_t cipher::size() const {
    return cols_; // rows_ is equal or differs by 1
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::vector<std::string> segments;
    for (std::size_t col = 0; col < cols_; ++col) {
        std::string segment;
        for (std::size_t row = 0; row < rows_; ++row) {
            std::size_t index = row * cols_ + col;
            if (index < normalized_.size()) {
                segment += normalized_[index];
            }
        }
        segments.push_back(std::move(segment));
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string result;
    for (std::size_t col = 0; col < cols_; ++col) {
        for (std::size_t row = 0; row < rows_; ++row) {
            std::size_t index = row * cols_ + col;
            if (index < normalized_.size()) {
                result += normalized_[index];
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string result;
    for (std::size_t col = 0; col < cols_; ++col) {
        for (std::size_t row = 0; row < rows_; ++row) {
            std::size_t index = row * cols_ + col;
            if (index < normalized_.size()) {
                result += normalized_[index];
            } else {
                result += ' ';
            }
        }
        if (col != cols_ - 1) {
            result += ' ';
        }
    }
    return result;
}

} // namespace crypto_square
