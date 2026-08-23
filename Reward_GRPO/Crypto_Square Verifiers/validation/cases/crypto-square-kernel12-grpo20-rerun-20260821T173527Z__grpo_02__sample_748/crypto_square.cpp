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
    return static_cast<std::size_t>(std::sqrt(text_.size()));
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::vector<std::string> segments;
    
    if (text_.empty()) {
        return segments;
    }

    std::size_t s = size();
    std::size_t cols = s;
    if (cols * cols < text_.size()) {
        ++cols;
    }
    std::size_t rows = cols;

    for (std::size_t r = 0; r < rows; ++r) {
        std::string segment;
        for (std::size_t c = 0; c < cols; ++c) {
            if (r * cols + c < text_.size()) {
                segment.push_back(text_[r * cols + c]);
            }
        }
        segments.push_back(segment);
    }

    return segments;
}

std::string cipher::cipher_text() const {
    std::string result;
    std::size_t cols = size();
    if (cols * cols < text_.size()) {
        ++cols;
    }
    std::size_t rows = cols;

    for (std::size_t c = 0; c < cols; ++c) {
        for (std::size_t r = 0; r < rows; ++r) {
            if (r * cols + c < text_.size()) {
                result.push_back(text_[r * cols + c]);
            }
        }
    }

    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string result = cipher_text();
    if (result.empty()) {
        return result;
    }
    
    std::vector<std::string> segments = plain_text_segments();
    std::ostringstream oss;
    for (size_t i = 0; i < segments.size(); ++i) {
        if (i != 0) {
            oss << " ";
        }
        oss << segments[i];
    }
    
    return oss.str();
}

}  // namespace crypto_square
