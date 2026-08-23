#include "crypto_square.h"

#include <cctype>
#include <numeric>

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
    if (text_.empty()) return {};

    std::size_t cols = size();
    std::size_t rows = (text_.size() + cols - 1) / cols;
    std::vector<std::string> segments;

    for (std::size_t r = 0; r < rows; ++r) {
        std::string segment;
        for (std::size_t c = 0; c < cols; ++c) {
            std::size_t index = r * cols + c;
            if (index < text_.size()) {
                segment += text_[index];
            }
        }
        segments.push_back(segment);
    }
    return segments;
}

std::string cipher::cipher_text() const {
    if (text_.empty()) return "";

    std::size_t cols = size();
    std::size_t rows = (text_.size() + cols - 1) / cols;
    std::string result;

    for (std::size_t c = 0; c < cols; ++c) {
        for (std::size_t r = 0; r < rows; ++r) {
            std::size_t index = r * cols + c;
            if (index < text_.size()) {
                result += text_[index];
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    if (text_.empty()) return "";

    std::size_t cols = size();
    std::size_t rows = (text_.size() + cols - 1) / cols;
    std::string result;

    for (std::size_t c = 0; c < cols; ++c) {
        for (std::size_t r = 0; r < rows; ++r) {
            std::size_t index = r * cols + c;
            if (index < text_.size()) {
                result += text_[index];
            } else {
                result += ' ';
            }
        }
        if (c < cols - 1) {
            result += ' ';
        }
    }
    return result;
}

}  // namespace crypto_square
