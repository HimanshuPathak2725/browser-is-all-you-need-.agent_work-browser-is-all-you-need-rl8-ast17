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

std::vector<std::string> cipher::plain_text_segments() const {
    std::vector<std::string> result;
    std::size_t cols = size();
    std::size_t rows = (text_.size() + cols - 1) / cols;

    for (std::size_t row = 0; row < rows; ++row) {
        std::size_t start = row * cols;
        std::size_t end = std::min(start + cols, text_.size());
        result.push_back(text_.substr(start, end - start));
    }
    return result;
}

std::string cipher::cipher_text() const {
    std::string result;
    std::size_t cols = size();
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
    std::size_t rows = (text_.size() + cols - 1) / cols;

    for (std::size_t row = 0; row < rows; ++row) {
        if (row != 0) result += ' ';
        std::size_t start = row * cols;
        std::size_t end = std::min(start + cols, text_.size());
        result += text_.substr(start, end - start);
    }
    return result;
}

}  // namespace crypto_square
