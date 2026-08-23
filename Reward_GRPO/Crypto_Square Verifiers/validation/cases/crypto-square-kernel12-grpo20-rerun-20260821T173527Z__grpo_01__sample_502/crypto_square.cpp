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
    for (char c : text_) {
        if (std::isalnum(static_cast<unsigned char>(c))) {
            result.push_back(std::tolower(static_cast<unsigned char>(c)));
        }
    }
    return result;
}

std::size_t cipher::size() const {
    std::string normalized = normalize_plain_text();
    if (normalized.empty()) return 0;
    return static_cast<std::size_t>(std::ceil(std::sqrt(normalized.size())));
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::string normalized = normalize_plain_text();
    std::size_t size_ = size();
    if (size_ == 0) return {};
    
    std::size_t num_rows = (normalized.size() + size_ - 1) / size_;
    std::vector<std::string> segments;
    segments.reserve(num_rows);
    
    for (std::size_t i = 0; i < num_rows; ++i) {
        std::size_t start = i * size_;
        std::size_t end = std::min(start + size_, normalized.size());
        segments.emplace_back(normalized.substr(start, end - start));
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string normalized = normalize_plain_text();
    std::size_t size_ = size();
    if (size_ == 0) return "";
    
    std::size_t num_rows = (normalized.size() + size_ - 1) / size_;
    std::string result;
    result.reserve(normalized.size());
    
    for (std::size_t col = 0; col < size_; ++col) {
        for (std::size_t row = 0; row < num_rows; ++row) {
            std::size_t idx = row * size_ + col;
            if (idx < normalized.size()) {
                result.push_back(normalized[idx]);
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string normalized = normalize_plain_text();
    std::size_t size_ = size();
    if (size_ == 0) return "";
    
    std::size_t num_rows = (normalized.size() + size_ - 1) / size_;
    std::string result;
    result.reserve(normalized.size());
    
    for (std::size_t col = 0; col < size_; ++col) {
        std::string segment;
        segment.reserve(num_rows);
        for (std::size_t row = 0; row < num_rows; ++row) {
            std::size_t idx = row * size_ + col;
            if (idx < normalized.size()) {
                segment.push_back(normalized[idx]);
            } else {
                segment.push_back(' ');
            }
        }
        result += segment;
        if (col < size_ - 1) {
            result += ' ';
        }
    }
    return result;
}

}  // namespace crypto_square
