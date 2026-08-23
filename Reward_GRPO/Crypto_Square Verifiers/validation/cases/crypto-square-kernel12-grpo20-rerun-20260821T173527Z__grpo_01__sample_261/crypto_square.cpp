#include "crypto_square.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <sstream>
#include <vector>

namespace crypto_square {

cipher::cipher(std::string const& text) {
    for (unsigned char character : text) {
        if (std::isalnum(character)) {
            text_.push_back(static_cast<char>(std::tolower(character)));
        }
    }
}

std::string cipher::normalize_plain_text() const { return text_; }

std::size_t cipher::size() const {
    if (text_.empty()) return 0;
    std::size_t len = text_.size();
    std::size_t s = static_cast<std::size_t>(std::sqrt(len));
    if (s * s < len) {
        ++s;
    }
    return s;
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::vector<std::string> segments;
    std::size_t segment_size = size();
    if (segment_size == 0) return segments;
    for (std::size_t i = 0; i < text_.size(); i += segment_size) {
        std::string seg = text_.substr(i, segment_size);
        while (seg.size() < segment_size) {
            seg.push_back(' ');
        }
        segments.push_back(seg);
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string result;
    std::size_t cols = size();
    if (cols == 0) return result;
    std::size_t rows = (text_.size() + cols - 1) / cols;
    for (std::size_t col = 0; col < cols; ++col) {
        for (std::size_t row = 0; row < rows; ++row) {
            std::size_t index = row * cols + col;
            if (index < text_.size()) {
                result.push_back(text_[index]);
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string result;
    std::size_t cols = size();
    if (cols == 0) return result;
    std::size_t rows = (text_.size() + cols - 1) / cols;
    for (std::size_t col = 0; col < cols; ++col) {
        std::string segment;
        for (std::size_t row = 0; row < rows; ++row) {
            std::size_t index = row * cols + col;
            if (index < text_.size()) {
                segment.push_back(text_[index]);
            } else {
                segment.push_back(' ');
            }
        }
        result += segment + " ";
    }
    if (!result.empty()) {
        result.pop_back();
    }
    return result;
}

}  // namespace crypto_square
