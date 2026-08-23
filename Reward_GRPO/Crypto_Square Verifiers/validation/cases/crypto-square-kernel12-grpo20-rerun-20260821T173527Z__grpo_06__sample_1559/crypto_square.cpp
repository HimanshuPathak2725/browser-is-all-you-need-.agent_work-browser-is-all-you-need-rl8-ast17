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
    if (text_.empty()) {
        return 0;
    }
    return static_cast<std::size_t>(std::ceil(std::sqrt(text_.size())));
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::vector<std::string> segments;
    std::size_t segment_size = size();
    if (segment_size == 0) {
        return segments;
    }
    for (std::size_t i = 0; i < text_.size(); i += segment_size) {
        segments.push_back(text_.substr(i, segment_size));
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string result;
    std::size_t segment_size = size();
    if (segment_size == 0) {
        return result;
    }
    for (std::size_t col = 0; col < segment_size; ++col) {
        for (std::size_t row = 0; row < text_.size(); ++row) {
            if (col < text_.size() - row * segment_size) {
                result += text_[row * segment_size + col];
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string result;
    std::vector<std::string> segments = plain_text_segments();
    std::size_t segment_size = size();
    if (segment_size == 0) {
        return result;
    }
    for (std::size_t col = 0; col < segment_size; ++col) {
        std::string segment;
        for (std::size_t row = 0; row < segments.size(); ++row) {
            if (col < segments[row].size()) {
                segment += segments[row][col];
            } else {
                segment += ' ';
            }
        }
        result += segment + ' ';
    }
    if (!result.empty()) {
        result.pop_back();
    }
    return result;
}

}  // namespace crypto_square
