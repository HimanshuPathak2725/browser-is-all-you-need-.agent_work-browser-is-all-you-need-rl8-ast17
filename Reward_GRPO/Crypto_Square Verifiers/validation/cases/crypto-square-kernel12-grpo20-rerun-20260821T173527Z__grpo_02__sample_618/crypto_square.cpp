#include "crypto_square.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <sstream>
#include <vector>

namespace crypto_square {

cipher::cipher(std::string const& text) : text_(text) {
    normalized_ = normalize_plain_text();
    size_ = std::size_t(std::ceil(std::sqrt(normalized_.size())));
}

std::string cipher::normalize_plain_text() const {
    std::string result;
    std::transform(
        text_.begin(), text_.end(), std::back_inserter(result),
        [](unsigned char c) { return std::isalnum(c) ? std::tolower(c) : c; });
    result.erase(
        std::remove_if(result.begin(), result.end(),
                       [](unsigned char c) { return !std::isalnum(c); }),
        result.end());
    return result;
}

std::size_t cipher::size() const { return size_; }

std::vector<std::string> cipher::plain_text_segments() const {
    std::vector<std::string> segments;
    for (std::size_t offset = 0; offset < normalized_.size(); offset += size_) {
        segments.push_back(normalized_.substr(offset, size_));
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string result;
    for (std::size_t col = 0; col < size_; ++col) {
        for (std::size_t row = 0; row < (normalized_.size() + size_ - 1) / size_; ++row) {
            const std::size_t index = row * size_ + col;
            if (index < normalized_.size()) {
                result += normalized_[index];
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string result;
    for (std::size_t col = 0; col < size_; ++col) {
        for (std::size_t row = 0; row < (normalized_.size() + size_ - 1) / size_; ++row) {
            const std::size_t index = row * size_ + col;
            if (index < normalized_.size()) {
                result += normalized_[index];
            } else {
                result += ' ';
            }
        }
        if (col != size_ - 1) {
            result += ' ';
        }
    }
    return result;
}

}  // namespace crypto_square
