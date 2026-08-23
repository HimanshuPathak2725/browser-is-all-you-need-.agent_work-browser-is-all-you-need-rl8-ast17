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
    normalized.reserve(text_.size());
    for (char c : text_) {
        if (std::isalnum(static_cast<unsigned char>(c))) {
            normalized.push_back(std::tolower(static_cast<unsigned char>(c)));
        }
    }
    return normalized;
}

std::size_t cipher::size() const {
    std::string normalized = normalize_plain_text();
    if (normalized.empty()) {
        return 0;
    }
    return static_cast<std::size_t>(std::ceil(std::sqrt(normalized.size())));
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::string normalized = normalize_plain_text();
    std::vector<std::string> segments;
    if (normalized.empty()) {
        return segments;
    }
    std::size_t segment_len = size();
    for (std::size_t i = 0; i < normalized.size(); i += segment_len) {
        segments.push_back(normalized.substr(i, segment_len));
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string normalized = normalize_plain_text();
    if (normalized.empty()) {
        return "";
    }
    std::string result;
    result.reserve(normalized.size());
    std::size_t cols = size();
    std::size_t rows = (normalized.size() + cols - 1) / cols;
    for (std::size_t col = 0; col < cols; ++col) {
        for (std::size_t row = 0; row < rows; ++row) {
            std::size_t index = col + row * cols;
            if (index < normalized.size()) {
                result.push_back(normalized[index]);
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string normalized = normalize_plain_text();
    if (normalized.empty()) {
        return "";
    }
    std::string result;
    std::size_t cols = size();
    std::size_t rows = (normalized.size() + cols - 1) / cols;
    for (std::size_t col = 0; col < cols; ++col) {
        std::string segment;
        for (std::size_t row = 0; row < rows; ++row) {
            std::size_t index = col + row * cols;
            if (index < normalized.size()) {
                segment.push_back(normalized[index]);
            } else {
                segment.push_back(' ');
            }
        }
        result += segment + " ";
    }
    result.pop_back(); // Remove trailing space
    return result;
}

}  // namespace crypto_square
