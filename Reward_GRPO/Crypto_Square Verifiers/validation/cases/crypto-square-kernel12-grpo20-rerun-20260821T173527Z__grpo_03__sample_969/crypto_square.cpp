#include "crypto_square.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <sstream>
#include <vector>

namespace crypto_square {

cipher::cipher(std::string const& text) : text_(text) {}

std::string const& cipher::get_normalized() const {
    if (normalized_.empty()) {
        std::transform(text_.begin(), text_.end(), std::back_inserter(normalized_),
                       [](unsigned char c) { return std::tolower(c); });
        normalized_.erase(std::remove_if(normalized_.begin(), normalized_.end(),
                                       [](unsigned char c) { return !std::isalnum(c); }),
                       normalized_.end());
    }
    return normalized_;
}

std::string cipher::normalize_plain_text() const {
    return get_normalized();
}

std::size_t cipher::size() const {
    std::string const& normalized = get_normalized();
    if (normalized.empty()) return 0;
    return static_cast<std::size_t>(std::ceil(std::sqrt(normalized.size())));
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::string const& normalized = get_normalized();
    std::vector<std::string> segments;
    std::size_t segment_size = size();
    for (std::size_t i = 0; i < normalized.size(); i += segment_size) {
        segments.push_back(normalized.substr(i, segment_size));
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string const& normalized = get_normalized();
    if (normalized.empty()) return "";
    std::size_t s = size();
    std::string result;
    for (std::size_t col = 0; col < s; ++col) {
        for (std::size_t row = 0; row < (normalized.size() + s - 1) / s; ++row) {
            std::size_t index = row * s + col;
            if (index < normalized.size()) {
                result.push_back(normalized[index]);
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string const& normalized = get_normalized();
    if (normalized.empty()) return "";
    std::size_t s = size();
    std::string result;
    for (std::size_t col = 0; col < s; ++col) {
        for (std::size_t row = 0; row < (normalized.size() + s - 1) / s; ++row) {
            std::size_t index = row * s + col;
            if (index < normalized.size()) {
                result.push_back(normalized[index]);
            } else {
                result.push_back(' ');
            }
        }
        if (col < s - 1) {
            result.push_back(' ');
        }
    }
    return result;
}

}  // namespace crypto_square
