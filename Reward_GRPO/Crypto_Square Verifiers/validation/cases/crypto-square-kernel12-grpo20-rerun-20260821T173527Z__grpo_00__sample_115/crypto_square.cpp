#include "crypto_square.h"

#include <cctype>

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
    std::size_t columns = 0;
    while (columns * columns < text_.size()) ++columns;
    return columns;
}

std::vector<std::string> cipher::plain_text_segments() const { return {text_}; }

std::string cipher::cipher_text() const {
    if (text_.empty()) {
        return "";
    }
    std::size_t cols = size();
    std::size_t rows = text_.size() / cols;
    std::string result;
    result.reserve(text_.size());
    
    for (std::size_t col = 0; col < cols; ++col) {
        for (std::size_t row = 0; row < rows; ++row) {
            result.push_back(text_[row * cols + col]);
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    if (text_.empty()) {
        return "";
    }
    std::string result = cipher_text();
    std::size_t cols = size();
    if (cols == 0) {
        return result;
    }
    std::size_t rows = text_.size() / cols;
    
    for (std::size_t col = 1; col < cols; ++col) {
        result.insert(col * rows, 1, ' ');
    }
    return result;
}

}  // namespace crypto_square
