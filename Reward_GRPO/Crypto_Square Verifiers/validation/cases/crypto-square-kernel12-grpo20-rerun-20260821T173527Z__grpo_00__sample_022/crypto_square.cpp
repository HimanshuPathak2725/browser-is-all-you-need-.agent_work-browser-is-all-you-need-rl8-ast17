#include "crypto_square.h"

#include <algorithm>
#include <cctype>
#include <cmath>

namespace crypto_square {

cipher::cipher(std::string const& text) : text_(text) {
    std::string result;
    std::transform(text_.begin(), text_.end(), std::back_inserter(result),
                   [](unsigned char c) { return std::tolower(c); });
    result.erase(std::remove_if(result.begin(), result.end(),
                               [](unsigned char c) { return !std::isalnum(c); }),
                   result.end());
    normalized_plain_ = result;
    if (normalized_plain_.empty()) {
        size_ = 0;
    } else {
        size_ = static_cast<std::size_t>(std::ceil(std::sqrt(normalized_plain_.size())));
    }
}

std::string cipher::normalize_plain_text() const {
    return normalized_plain_;
}

std::size_t cipher::size() const {
    return size_;
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::vector<std::string> segments;
    for (std::size_t i = 0; i < normalized_plain_.size(); i += size_) {
        segments.push_back(normalized_plain_.substr(i, size_));
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string result;
    for (std::size_t col = 0; col < size_; ++col) {
        for (std::size_t row = 0; row < size_; ++row) {
            const std::size_t index = row * size_ + col;
            if (index < normalized_plain_.size()) {
                result += normalized_plain_[index];
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string result;
    for (std::size_t col = 0; col < size_; ++col) {
        for (std::size_t row = 0; row < size_; ++row) {
            const std::size_t index = row * size_ + col;
            if (index < normalized_plain_.size()) {
                result += normalized_plain_[index];
            } else {
                result += ' ';
            }
        }
        if (col < size_ - 1) {
            result += " ";
        }
    }
    return result;
}

}  // namespace crypto_square
