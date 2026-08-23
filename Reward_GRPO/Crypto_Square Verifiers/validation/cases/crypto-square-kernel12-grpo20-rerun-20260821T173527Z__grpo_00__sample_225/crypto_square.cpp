#include "crypto_square.h"

#include <cctype>
#include <cmath>
#include <vector>

namespace crypto_square {

cipher::cipher(std::string const& text) {
    for (char const& c : text) {
        if (std::isalnum(c)) {
            normalized_ += static_cast<char>(std::tolower(c));
        }
    }

    if (normalized_.empty()) {
        size_ = 0;
    } else {
        size_ = static_cast<std::size_t>(std::ceil(std::sqrt(normalized_.size())));
    }

    if (normalized_.empty()) {
        return;
    }

    for (std::size_t i = 0; i < normalized_.size(); i += size_) {
        segments_.push_back(normalized_.substr(i, size_));
    }
}

std::string cipher::normalize_plain_text() const {
    return normalized_;
}

std::size_t cipher::size() const {
    return size_;
}

std::vector<std::string> cipher::plain_text_segments() const {
    return segments_;
}

std::string cipher::cipher_text() const {
    std::string result;
    if (normalized_.empty()) {
        return result;
    }

    for (std::size_t col = 0; col < size_; ++col) {
        for (std::size_t row = 0; row < (normalized_.size() + size_ - 1) / size_; ++row) {
            std::size_t index = row * size_ + col;
            if (index < normalized_.size()) {
                result += normalized_[index];
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string result;
    if (normalized_.empty()) {
        return result;
    }

    for (std::size_t col = 0; col < size_; ++col) {
        std::string segment;
        for (std::size_t row = 0; row < (normalized_.size() + size_ - 1) / size_; ++row) {
            std::size_t index = row * size_ + col;
            if (index < normalized_.size()) {
                segment += normalized_[index];
            } else {
                segment += ' ';
            }
        }
        if (!segment.empty()) {
            result += segment;
            result += ' ';
        }
    }
    if (!result.empty()) {
        result.pop_back();
    }
    return result;
}

}  // namespace crypto_square
