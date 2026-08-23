#include "crypto_square.h"

#include <algorithm>
#include <cmath>
#include <cctype>
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
    return static_cast<std::size_t>(std::ceil(std::sqrt(text_.size())));
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::vector<std::string> segments;
    if (text_.empty()) return segments;
    std::size_t segment_size = size();
    for (std::size_t i = 0; i < text_.size(); i += segment_size) {
        segments.push_back(text_.substr(i, segment_size));
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string result;
    if (text_.empty()) return result;
    std::size_t size = this->size();
    std::size_t rows = (text_.size() + size - 1) / size;
    for (std::size_t col = 0; col < size; ++col) {
        for (std::size_t row = 0; row < rows; ++row) {
            std::size_t index = row * size + col;
            if (index < text_.size()) {
                result.push_back(text_[index]);
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string result;
    if (text_.empty()) return result;
    std::size_t size = this->size();
    std::size_t rows = (text_.size() + size - 1) / size;
    for (std::size_t col = 0; col < size; ++col) {
        for (std::size_t row = 0; row < rows; ++row) {
            std::size_t index = row * size + col;
            if (index < text_.size()) {
                result.push_back(text_[index]);
            } else {
                result.push_back(' ');
            }
        }
        if (col != size - 1) {
            result.push_back(' ');
        }
    }
    return result;
}

}  // namespace crypto_square
