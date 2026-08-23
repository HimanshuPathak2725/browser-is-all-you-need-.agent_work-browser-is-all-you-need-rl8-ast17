#include "crypto_square.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <vector>

namespace crypto_square {

cipher::cipher(std::string const& text) : text_(text) {}

std::string cipher::normalize_plain_text() const {
    std::string normalized;
    for (char c : text_) {
        if (std::isalnum(c)) {
            normalized += static_cast<char>(std::tolower(c));
        }
    }
    return normalized;
}

std::size_t cipher::size() const {
    std::string normalized = normalize_plain_text();
    if (normalized.empty()) return 0;
    std::size_t n = normalized.size();
    std::size_t cols = static_cast<std::size_t>(std::ceil(std::sqrt(n)));
    std::size_t rows = (n + cols - 1) / cols;
    if (cols < rows) {
        cols = rows;
        rows = (n + cols - 1) / cols;
    }
    return cols;
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::string normalized = normalize_plain_text();
    if (normalized.empty()) return {};
    std::size_t cols = size();
    std::size_t rows = (normalized.size() + cols - 1) / cols;
    std::vector<std::string> segments;
    for (std::size_t r = 0; r < rows; ++r) {
        std::string segment;
        for (std::size_t c = 0; c < cols; ++c) {
            if (r * cols + c < normalized.size()) {
                segment += normalized[r * cols + c];
            }
        }
        segments.push_back(segment);
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string normalized = normalize_plain_text();
    if (normalized.empty()) return {};
    std::string result;
    std::size_t cols = size();
    std::size_t rows = (normalized.size() + cols - 1) / cols;
    for (std::size_t c = 0; c < cols; ++c) {
        for (std::size_t r = 0; r < rows; ++r) {
            if (r * cols + c < normalized.size()) {
                result += normalized[r * cols + c];
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string normalized = normalize_plain_text();
    if (normalized.empty()) return {};
    std::string result;
    std::size_t cols = size();
    std::size_t rows = (normalized.size() + cols - 1) / cols;
    for (std::size_t c = 0; c < cols; ++c) {
        for (std::size_t r = 0; r < rows; ++r) {
            if (r * cols + c < normalized.size()) {
                result += normalized[r * cols + c];
            } else {
                result += " ";
            }
        }
        if (c < cols - 1) {
            result += " ";
        }
    }
    return result;
}

}  // namespace crypto_square
