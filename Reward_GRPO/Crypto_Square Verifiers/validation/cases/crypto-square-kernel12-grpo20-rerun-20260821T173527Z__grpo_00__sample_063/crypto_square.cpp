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
    if (columns * (columns + 1) >= text_.size()) {
        return columns + 1;
    }
    return columns;
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::vector<std::string> segments;
    std::size_t columns = size();
    std::size_t rows = text_.size() / columns;
    for (std::size_t col = 0; col < columns; ++col) {
        std::string segment;
        for (std::size_t row = 0; row < rows; ++row) {
            segment.push_back(text_[col * rows + row]);
        }
        segments.push_back(segment);
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string result;
    std::size_t columns = size();
    std::size_t rows = text_.size() / columns;
    for (std::size_t col = 0; col < columns; ++col) {
        for (std::size_t row = 0; row < rows; ++row) {
            std::size_t index = col * rows + row;
            if (index < text_.size()) {
                result.push_back(text_[index]);
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string result = cipher_text();
    std::size_t columns = size();
    std::size_t rows = text_.size() / columns;
    for (std::size_t segment = 1; segment < columns; ++segment) {
        std::size_t insert_pos = segment * rows + rows;
        if (insert_pos < result.size()) {
            result.insert(insert_pos, 1, ' ');
        }
    }
    return result;
}

}  // namespace crypto_square
