#include "crypto_square.h"

#include <algorithm>
#include <cctype>
#include <cmath>

namespace crypto_square {

cipher::cipher(std::string const& text) : text_(text) {
    // Normalize the input text
    std::string normalized;
    for (char c : text_) {
        if (std::isalnum(c)) {
            normalized += static_cast<char>(std::tolower(c));
        }
    }
    normalized_ = normalized;

    // Calculate rectangle dimensions
    std::size_t n = normalized_.size();
    if (n == 0) {
        col_count_ = 0;
        row_count_ = 0;
    } else {
        std::size_t root = static_cast<std::size_t>(std::ceil(std::sqrt(n)));
        col_count_ = root;
        row_count_ = (n + root - 1) / root;
    }
}

std::string cipher::normalize_plain_text() const { return normalized_; }

std::size_t cipher::size() const { return col_count_; }

std::vector<std::string> cipher::plain_text_segments() const {
    std::vector<std::string> segments;
    for (std::size_t r = 0; r < row_count_; ++r) {
        std::string segment;
        for (std::size_t c = 0; c < col_count_; ++c) {
            std::size_t idx = r * col_count_ + c;
            if (idx < normalized_.size()) {
                segment += normalized_[idx];
            }
        }
        segments.push_back(segment);
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string result;
    for (std::size_t c = 0; c < col_count_; ++c) {
        for (std::size_t r = 0; r < row_count_; ++r) {
            std::size_t idx = r * col_count_ + c;
            if (idx < normalized_.size()) {
                result += normalized_[idx];
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::vector<std::string> segments;
    for (std::size_t c = 0; c < col_count_; ++c) {
        std::string segment;
        for (std::size_t r = 0; r < row_count_; ++r) {
            std::size_t idx = r * col_count_ + c;
            if (idx < normalized_.size()) {
                segment += normalized_[idx];
            } else {
                segment += ' ';
            }
        }
        segments.push_back(segment);
    }
    // Join segments with spaces
    std::string result;
    for (const auto& s : segments) {
        if (!result.empty()) result += ' ';
        result += s;
    }
    return result;
}

}  // namespace crypto_square
