#include "crypto_square.h"

#include <cmath>
#include <sstream>
#include <utility>

namespace crypto_square {

cipher::cipher(std::string const& text) : text_(text) {}

std::string cipher::normalize_plain_text() const {
    std::string normalized;
    normalized.reserve(text_.size());
    for (const char c : text_) {
        if (std::isalnum(static_cast<unsigned char>(c))) {
            normalized += static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
        }
    }
    return normalized;
}

std::size_t cipher::size() const {
    const std::string normalized = normalize_plain_text();
    if (normalized.empty()) {
        return 0;
    }
    return static_cast<std::size_t>(std::ceil(std::sqrt(normalized.size())));
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::vector<std::string> segments;
    const std::string normalized = normalize_plain_text();
    const std::size_t n = size();
    if (n == 0) {
        return segments;
    }
    const std::size_t rows = (normalized.size() + n - 1) / n;
    for (std::size_t row = 0; row < rows; ++row) {
        segments.push_back(normalized.substr(row * n, n));
    }
    return segments;
}

std::string cipher::cipher_text() const {
    const std::string normalized = normalize_plain_text();
    const std::size_t n = size();
    if (n == 0) {
        return "";
    }
    const std::size_t rows = (normalized.size() + n - 1) / n;
    std::string result;
    result.reserve(normalized.size());
    for (std::size_t col = 0; col < n; ++col) {
        for (std::size_t row = 0; row < rows; ++row) {
            if (row * n + col < normalized.size()) {
                result += normalized[row * n + col];
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    const std::string normalized = normalize_plain_text();
    const std::size_t n = size();
    if (n == 0) {
        return "";
    }
    const std::size_t rows = (normalized.size() + n - 1) / n;
    std::vector<std::string> segments;
    for (std::size_t col = 0; col < n; ++col) {
        std::string segment;
        for (std::size_t row = 0; row < rows; ++row) {
            if (row * n + col < normalized.size()) {
                segment += normalized[row * n + col];
            } else {
                segment += ' ';
            }
        }
        segments.push_back(std::move(segment));
    }
    std::string result;
    for (const auto& segment : segments) {
        result += segment + " ";
    }
    if (!result.empty()) {
        result.pop_back();
    }
    return result;
}

}  // namespace crypto_square
