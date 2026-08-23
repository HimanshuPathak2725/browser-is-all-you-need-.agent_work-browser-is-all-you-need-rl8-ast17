#include "crypto_square.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <vector>

namespace crypto_square {

cipher::cipher(std::string const& text) : text_(text) {
    std::string normalized;
    std::transform(text_.begin(), text_.end(), std::back_inserter(normalized),
                   [](unsigned char c) { return std::tolower(c); });
    normalized_.erase(
        std::remove_if(normalized_.begin(), normalized_.end(),
                       [](unsigned char c) { return !std::isalnum(c); }),
        normalized_.end());
    size_ = static_cast<std::size_t>(std::ceil(std::sqrt(normalized_.size())));
}

std::string cipher::normalize_plain_text() const { return normalized_; }

std::size_t cipher::size() const { return size_; }

std::vector<std::string> cipher::plain_text_segments() const {
    std::vector<std::string> segments;
    for (std::size_t i = 0; i < normalized_.size(); i += size_) {
        segments.push_back(normalized_.substr(i, size_));
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string cipher;
    cipher.reserve(normalized_.size());
    for (std::size_t col = 0; col < size_; ++col) {
        for (std::size_t row = 0; row < size_; ++row) {
            std::size_t index = col + row * size_;
            if (index < normalized_.size()) {
                cipher += normalized_[index];
            }
        }
    }
    return cipher;
}

std::string cipher::normalized_cipher_text() const {
    std::string normalized_cipher;
    normalized_cipher.reserve(normalized_.size() + (size_ - 1));
    for (std::size_t col = 0; col < size_; ++col) {
        for (std::size_t row = 0; row < size_; ++row) {
            std::size_t index = col + row * size_;
            if (index < normalized_.size()) {
                normalized_cipher += normalized_[index];
            }
        }
        if (col != size_ - 1) {
            normalized_cipher += ' ';
        }
    }
    return normalized_cipher;
}

}  // namespace crypto_square
