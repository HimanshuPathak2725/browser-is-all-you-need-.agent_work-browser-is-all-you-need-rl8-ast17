#include "crypto_square.h"

#include <cctype>
#include <cmath>

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
    calculate_dimensions();
    return cols_;
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::vector<std::string> segments;
    if (cols_ == 0) return segments;
    calculate_dimensions();
    for (std::size_t col = 0; col < cols_; ++col) {
        std::string segment;
        for (std::size_t row = 0; row < rows_; ++row) {
            std::size_t index = col * rows_ + row;
            if (index < text_.size()) {
                segment += text_[index];
            }
        }
        segments.push_back(segment);
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string result;
    if (cols_ == 0) return result;
    calculate_dimensions();
    for (std::size_t col = 0; col < cols_; ++col) {
        for (std::size_t row = 0; row < rows_; ++row) {
            std::size_t index = col * rows_ + row;
            if (index < text_.size()) {
                result += text_[index];
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string result;
    if (cols_ == 0) return result;
    calculate_dimensions();
    for (std::size_t col = 0; col < cols_; ++col) {
        for (std::size_t row = 0; row < rows_; ++row) {
            std::size_t index = col * rows_ + row;
            if (index < text_.size()) {
                result += text_[index];
            } else {
                result += ' ';
            }
        }
        if (col < cols_ - 1) {
            result += ' ';
        }
    }
    return result;
}

void cipher::calculate_dimensions() const {
    if (cols_ != 0) {
        return;
    }
    if (text_.empty()) {
        cols_ = rows_ = 0;
        return;
    }
    std::size_t len = text_.size();
    cols_ = std::ceil(std::sqrt(len));
    if (cols_ * cols_ < len) {
        ++cols_;
    }
    rows_ = cols_;
}

}  // namespace crypto_square
