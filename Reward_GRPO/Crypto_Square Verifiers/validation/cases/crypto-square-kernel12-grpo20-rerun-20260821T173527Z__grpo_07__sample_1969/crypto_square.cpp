#include "crypto_square.h"

#include <algorithm>
#include <cctype>
#include <cmath>

namespace crypto_square {

cipher::cipher(std::string const& text) : text_(text) {}

std::string cipher::normalize_plain_text() const {
    std::string result;
    std::transform(text_.begin(), text_.end(), std::back_inserter(result),
                   [](unsigned char c) { return std::tolower(c); });
    result.erase(std::remove_if(result.begin(), result.end(),
                               [](unsigned char c) { return !std::isalnum(c); }), result.end());
    return result;
}

std::size_t cipher::size() const {
    std::string normalized = normalize_plain_text();
    return static_cast<std::size_t>(std::ceil(std::sqrt(normalized.size())));
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::string normalized = normalize_plain_text();
    std::vector<std::string> segments;
    std::size_t segment_size = size();
    for (std::size_t i = 0; i < normalized.size(); i += segment_size) {
        segments.push_back(normalized.substr(i, segment_size));
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string normalized = normalize_plain_text();
    std::string result;
    std::size_t segment_size = size();
    if (normalized.empty()) return result;

    std::size_t rows = (normalized.size() + segment_size - 1) / segment_size;
    for (std::size_t col = 0; col < segment_size; ++col) {
        for (std::size_t row = 0; row < rows; ++row) {
            std::size_t index = row * segment_size + col;
            if (index < normalized.size()) {
                result += normalized[index];
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string normalized = normalize_plain_text();
    std::string result;
    std::size_t segment_size = size();
    if (normalized.empty()) return result;

    std::size_t rows = normalized.size() / segment_size;
    if (normalized.size() % segment_size != 0) ++rows;

    std::string padded = normalized;
    if (normalized.size() % segment_size != 0) {
        padded += std::string(segment_size - (normalized.size() % segment_size), ' ');
    }

    for (std::size_t col = 0; col < segment_size; ++col) {
        std::string segment;
        for (std::size_t row = 0; row < rows; ++row) {
            segment += padded[row * segment_size + col];
        }
        result += segment + " ";
    }
    if (!result.empty()) result.pop_back();
    return result;
}

}  // namespace crypto_square
