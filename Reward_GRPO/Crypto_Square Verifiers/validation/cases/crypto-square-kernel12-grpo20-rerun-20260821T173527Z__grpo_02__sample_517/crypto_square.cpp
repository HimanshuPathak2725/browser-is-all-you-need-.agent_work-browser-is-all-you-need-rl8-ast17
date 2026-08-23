#include "crypto_square.h"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <string>
#include <vector>

namespace crypto_square {

cipher::cipher(std::string const& text) : text_(text) {}

std::string cipher::normalize_plain_text() const {
    if (!normalized_.empty()) {
        return normalized_;
    }
    for (char c : text_) {
        if (std::isalnum(static_cast<unsigned char>(c))) {
            normalized_ += std::tolower(static_cast<unsigned char>(c));
        }
    }
    return normalized_;
}

std::size_t cipher::size() const {
    std::size_t len = normalize_plain_text().size();
    return static_cast<std::size_t>(std::ceil(std::sqrt(len)));
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::string const& normalized = normalize_plain_text();
    std::vector<std::string> segments;
    std::size_t segment_size = size();
    for (std::size_t i = 0; i < normalized.size(); i += segment_size) {
        segments.push_back(normalized.substr(i, segment_size));
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string result;
    std::size_t segment_size = size();
    for (std::size_t col = 0; col < segment_size; ++col) {
        for (std::size_t row = 0; row < normalized_.size(); row += segment_size) {
            if (col + row < normalized_.size()) {
                result += normalized_[col + row];
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string result;
    std::string const& normalized = normalize_plain_text();
    std::size_t segment_size = size();
    for (std::size_t col = 0; col < segment_size; ++col) {
        for (std::size_t row = 0; row < normalized.size(); row += segment_size) {
            if (col + row < normalized.size()) {
                result += normalized[col + row];
            } else {
                result += ' ';
            }
        }
        if (col < segment_size - 1) {
            result += ' ';
        }
    }
    return result;
}

}  // namespace crypto_square
