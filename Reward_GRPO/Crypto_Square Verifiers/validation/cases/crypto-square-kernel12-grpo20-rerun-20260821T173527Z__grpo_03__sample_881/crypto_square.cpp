#include "crypto_square.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <vector>

namespace crypto_square {

cipher::cipher(std::string const& text) : text_(text) {}

std::string cipher::normalize_plain_text() const {
    precompute();
    return normalized_;
}

std::size_t cipher::size() const {
    precompute();
    return size_;
}

std::vector<std::string> cipher::plain_text_segments() const {
    precompute();
    return segments_;
}

std::string cipher::cipher_text() const {
    precompute();
    std::string result;
    result.reserve(normalized_.size());
    for (std::size_t col = 0; col < size_; ++col) {
        for (std::size_t row = 0; row < segments_.size(); ++row) {
            if (col < segments_[row].size()) {
                result.push_back(segments_[row][col]);
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    precompute();
    if (normalized_.empty()) return "";
    std::string result;
    for (std::size_t col = 0; col < size_; ++col) {
        if (col != 0) result.push_back(' ');
        std::string segment = cipher_text().substr(col * size_, size_);
        while (segment.size() < size_) {
            segment.push_back(' ');
        }
        result += segment;
    }
    return result;
}

void cipher::precompute() const {
    if (precomputed_) return;
    
    std::string normalized;
    for (char c : text_) {
        if (std::isalnum(c)) normalized.push_back(std::tolower(c));
    }
    normalized_ = normalized;
    
    if (normalized_.empty()) {
        size_ = 0;
        segments_.clear();
        precomputed_ = true;
        return;
    }
    
    size_ = static_cast<std::size_t>(std::ceil(std::sqrt(normalized_.size())));
    
    segments_.clear();
    for (std::size_t i = 0; i < normalized_.size(); i += size_) {
        segments_.push_back(normalized_.substr(i, size_));
    }
    
    precomputed_ = true;
}

}  // namespace crypto_square
