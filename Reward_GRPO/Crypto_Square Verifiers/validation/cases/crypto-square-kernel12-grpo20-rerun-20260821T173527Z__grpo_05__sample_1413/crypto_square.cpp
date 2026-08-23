#include "crypto_square.h"

#include <cctype>
#include <cmath>
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
    std::size_t const n = text_.size();
    std::size_t side = 1;
    while (side * side < n) ++side;
    return side;
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::vector<std::string> segments;
    std::size_t const segment_size = size();
    if (segment_size == 0) return segments;

    for (std::size_t i = 0; i < text_.size(); i += segment_size) {
        segments.emplace_back(text_.substr(i, segment_size));
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string result;
    std::size_t const side = size();
    if (side == 0) return result;

    for (std::size_t col = 0; col < side; ++col) {
        for (std::size_t row = 0; row < text_.size(); ++row) {
            std::size_t const index = row * side + col;
            if (index < text_.size()) {
                result += text_[index];
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string result;
    std::size_t const side = size();
    if (side == 0) return result;

    for (std::size_t col = 0; col < side; ++col) {
        if (col != 0) result += ' ';
        for (std::size_t row = 0; row < text_.size(); ++row) {
            std::size_t const index = row * side + col;
            if (index < text_.size()) {
                result += text_[index];
            }
        }
    }
    return result;
}

}  // namespace crypto_square
