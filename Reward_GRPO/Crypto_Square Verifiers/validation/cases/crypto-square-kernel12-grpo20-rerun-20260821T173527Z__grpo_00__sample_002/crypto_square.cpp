#include "crypto_square.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <vector>

namespace crypto_square {

cipher::cipher(std::string const& text) : text_(text) {}

std::string cipher::normalize_plain_text() const {
    std::string result;
    result.reserve(text_.size());
    std::transform(text_.begin(), text_.end(), std::back_inserter(result),
                   [](unsigned char c) { return std::isalnum(c) ? std::tolower(c) : c; });
    result.erase(std::remove_if(result.begin(), result.end(),
                                [](unsigned char c) { return !std::isalnum(c); }),
                 result.end());
    return result;
}

std::size_t cipher::size() const {
    std::string const& norm = normalize_plain_text();
    return static_cast<std::size_t>(std::ceil(std::sqrt(norm.size())));
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::string const& norm = normalize_plain_text();
    std::vector<std::string> segments;
    std::size_t n = size();
    for (std::size_t col = 0; col < n; ++col) {
        std::string segment;
        segment.reserve(n);
        for (std::size_t row = 0; row < n; ++row) {
            std::size_t index = row * n + col;
            if (index < norm.size()) {
                segment.push_back(norm[index]);
            }
        }
        segments.push_back(segment);
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::vector<std::string> segments = plain_text_segments();
    std::string result;
    for (std::string const& segment : segments) {
        result += segment;
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string result = cipher_text();
    std::size_t n = size();
    for (std::size_t col = 1; col < n; ++col) {
        result.insert(col * n, 1, ' ');
    }
    return result;
}

}  // namespace crypto_square
