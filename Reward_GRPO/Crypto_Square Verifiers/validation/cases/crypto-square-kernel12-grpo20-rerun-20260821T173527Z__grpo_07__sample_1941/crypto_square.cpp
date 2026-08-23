#include "crypto_square.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <sstream>
#include <stdexcept>
#include <vector>

namespace crypto_square {

cipher::cipher(std::string const& text) : text_(text) {}

std::string cipher::normalize_plain_text() const {
    std::string normalized;
    std::transform(text_.begin(), text_.end(), std::back_inserter(normalized),
                   [](unsigned char c) { return std::tolower(c); });
    normalized.erase(
        std::remove_if(normalized.begin(), normalized.end(),
                       [](unsigned char c) { return !std::isalnum(c); }),
        normalized.end());
    return normalized;
}

std::size_t cipher::size() const {
    std::string normalized = normalize_plain_text();
    if (normalized.empty()) {
        return 0;
    }
    std::size_t length = normalized.size();
    std::size_t cols = static_cast<std::size_t>(std::ceil(std::sqrt(length)));
    // Find smallest cols such that cols >= rows and cols - rows <= 1
    for (; cols <= length; ++cols) {
        std::size_t rows = (length + cols - 1) / cols;
        if (cols >= rows && cols - rows <= 1) {
            return cols;
        }
    }
    return cols; // Should not reach here
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::string normalized = normalize_plain_text();
    std::vector<std::string> segments;
    std::size_t seg_size = size();
    if (seg_size == 0) {
        return segments;
    }
    for (std::size_t i = 0; i < normalized.size(); i += seg_size) {
        segments.push_back(normalized.substr(i, seg_size));
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string normalized = normalize_plain_text();
    std::string result;
    std::size_t seg_size = size();
    for (std::size_t col = 0; col < seg_size; ++col) {
        for (std::size_t row = 0; row < normalized.size(); ++row) {
            std::size_t index = col + row * seg_size;
            if (index < normalized.size()) {
                result.push_back(normalized[index]);
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string normalized = normalize_plain_text();
    std::string result;
    std::size_t seg_size = size();
    if (seg_size == 0) {
        return result;
    }
    std::size_t rows = (normalized.size() + seg_size - 1) / seg_size;
    for (std::size_t col = 0; col < seg_size; ++col) {
        std::string segment;
        for (std::size_t row = 0; row < rows; ++row) {
            std::size_t index = row * seg_size + col;
            if (index < normalized.size()) {
                segment.push_back(normalized[index]);
            } else {
                segment.push_back(' ');
            }
        }
        result += segment;
        if (col != seg_size - 1) {
            result += ' ';
        }
    }
    return result;
}

}  // namespace crypto_square
