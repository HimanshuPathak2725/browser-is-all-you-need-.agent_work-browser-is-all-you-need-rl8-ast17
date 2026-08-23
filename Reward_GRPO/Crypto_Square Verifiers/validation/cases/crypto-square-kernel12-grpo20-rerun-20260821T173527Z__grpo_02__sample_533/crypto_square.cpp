#include "crypto_square.h"

#include <algorithm>
#include <cmath>
#include <cctype>
#include <sstream>
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
    return normalize_plain_text().size();
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::string normalized = normalize_plain_text();
    std::vector<std::string> segments;
    if (normalized.empty()) return segments;

    std::size_t cols = static_cast<std::size_t>(std::ceil(std::sqrt(normalized.size())));
    std::size_t rows = cols;
    if (cols * rows < normalized.size()) {
        rows--;
    }

    for (std::size_t i = 0; i < normalized.size(); i += cols) {
        segments.push_back(normalized.substr(i, cols));
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string normalized = normalize_plain_text();
    std::string result;
    if (normalized.empty()) return result;

    std::size_t cols = static_cast<std::size_t>(std::ceil(std::sqrt(normalized.size())));
    std::size_t rows = cols;
    if (cols * rows < normalized.size()) {
        rows--;
    }

    for (std::size_t c = 0; c < cols; ++c) {
        for (std::size_t r = 0; r < rows; ++r) {
            std::size_t index = r * cols + c;
            if (index < normalized.size()) {
                result.push_back(normalized[index]);
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string cipher = cipher_text();
    std::string result;
    if (cipher.empty()) return result;

    std::size_t cols = static_cast<std::size_t>(std::ceil(std::sqrt(cipher.size())));
    std::size_t rows = cipher.size() / cols;
    if (cols < rows || cols - rows > 1) {
        rows = cols - 1;
    }

    for (std::size_t i = 0; i < cipher.size(); i += rows) {
        result += cipher.substr(i, rows) + " ";
    }
    result.pop_back(); // Remove trailing space
    return result;
}

}  // namespace crypto_square
