#include "crypto_square.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <vector>
#include <string>

namespace crypto_square {

cipher::cipher(std::string const& text) : text_(text) {}

std::string cipher::normalize_plain_text() const {
    std::string result;
    result.reserve(text_.size());
    for (char c : text_) {
        if (std::isalnum(c)) {
            result.push_back(std::tolower(c));
        }
    }
    return result;
}

std::size_t cipher::size() const {
    std::string normalized = normalize_plain_text();
    std::size_t n = normalized.size();
    if (n == 0) return 0;
    return static_cast<std::size_t>(std::ceil(std::sqrt(n)));
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::string normalized = normalize_plain_text();
    std::size_t n = normalized.size();
    if (n == 0) return {};

    std::size_t side = size();
    std::size_t cols = (n + side - 1) / side;
    if (cols < side) {
        side = cols;
        cols = (n + side - 1) / side;
    }
    std::size_t rows = side;

    std::vector<std::string> segments;
    for (std::size_t row = 0; row < rows; ++row) {
        std::string segment;
        for (std::size_t col = 0; col < cols; ++col) {
            std::size_t index = row * cols + col;
            if (index < n) {
                segment.push_back(normalized[index]);
            }
        }
        segments.push_back(segment);
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string normalized = normalize_plain_text();
    std::size_t n = normalized.size();
    if (n == 0) return {};

    std::size_t side = size();
    std::size_t cols = (n + side - 1) / side;
    if (cols < side) {
        side = cols;
        cols = (n + side - 1) / side;
    }
    std::size_t rows = side;

    std::string result;
    for (std::size_t col = 0; col < cols; ++col) {
        for (std::size_t row = 0; row < rows; ++row) {
            std::size_t index = row * cols + col;
            if (index < n) {
                result.push_back(normalized[index]);
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string normalized = normalize_plain_text();
    std::size_t n = normalized.size();
    if (n == 0) return {};

    std::size_t side = size();
    std::size_t cols = (n + side - 1) / side;
    if (cols < side) {
        side = cols;
        cols = (n + side - 1) / side;
    }
    std::size_t rows = side;

    std::vector<std::string> segments;
    for (std::size_t row = 0; row < rows; ++row) {
        std::string segment;
        for (std::size_t col = 0; col < cols; ++col) {
            std::size_t index = row * cols + col;
            if (index < n) {
                segment.push_back(normalized[index]);
            }
        }
        segments.push_back(segment);
    }

    if (segments.empty()) return "";

    std::string result;
    for (std::size_t i = 0; i < segments.size(); ++i) {
        if (i != 0) result += " ";
        result += segments[i];
    }
    return result;
}

}  // namespace crypto_square
