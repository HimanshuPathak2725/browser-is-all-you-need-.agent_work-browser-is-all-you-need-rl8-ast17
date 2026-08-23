#include "crypto_square.h"

#include <cctype>
#include <cmath>
#include <sstream>
#include <vector>

namespace crypto_square {

cipher::cipher(std::string const& text) {
    // Normalize: keep only alphanumeric, convert to lowercase
    std::string normalized;
    for (char c : text) {
        if (std::isalnum(static_cast<unsigned char>(c))) {
            normalized += static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
        }
    }
    normalized_ = normalized;

    // Calculate dimensions: smallest rectangle where cols >= rows and diff <= 1
    if (normalized_.empty()) {
        cols_ = 0;
        rows_ = 0;
        return;
    }
    std::size_t length = normalized_.size();
    cols_ = static_cast<std::size_t>(std::ceil(std::sqrt(length)));
    rows_ = (length + cols_ - 1) / cols_; // ceil(length/cols)
}

std::string cipher::normalize_plain_text() const {
    return normalized_;
}

std::size_t cipher::size() const {
    return cols_; // or rows_, they are equal
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::vector<std::string> result;
    if (normalized_.empty()) return result;

    for (std::size_t r = 0; r < rows_; ++r) {
        std::size_t start = r * cols_;
        std::size_t end = std::min(start + cols_, normalized_.size());
        result.push_back(normalized_.substr(start, end - start));
    }
    return result;
}

std::string cipher::cipher_text() const {
    std::string result;
    if (normalized_.empty()) return result;

    for (std::size_t c = 0; c < cols_; ++c) {
        for (std::size_t r = 0; r < rows_; ++r) {
            std::size_t index = r * cols_ + c;
            if (index < normalized_.size()) {
                result += normalized_[index];
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string result;
    if (normalized_.empty()) return result;

    for (std::size_t c = 0; c < cols_; ++c) {
        std::string segment;
        for (std::size_t r = 0; r < rows_; ++r) {
            std::size_t index = r * cols_ + c;
            if (index < normalized_.size()) {
                segment += normalized_[index];
            } else {
                segment += ' '; // Preserve padding
            }
        }
        if (!segment.empty()) {
            result += segment + " ";
        }
    }
    // Remove trailing space
    if (!result.empty()) {
        result.pop_back();
    }
    return result;
}

} // namespace crypto_square
