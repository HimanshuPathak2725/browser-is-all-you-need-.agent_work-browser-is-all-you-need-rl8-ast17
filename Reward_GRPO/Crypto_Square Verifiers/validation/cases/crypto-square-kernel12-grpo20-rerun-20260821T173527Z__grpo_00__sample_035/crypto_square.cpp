#include "crypto_square.h"

#include <cctype>
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
    std::size_t columns = 0;
    while (columns * columns < text_.size()) ++columns;
    return columns;
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::vector<std::string> segments;
    for (std::size_t i = 0; i < text_.size(); i += size()) {
        segments.push_back(text_.substr(i, size()));
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string result;
    for (std::size_t col = 0; col < size(); ++col) {
        for (std::size_t row = 0; row < text_.size(); ++row) {
            std::size_t index = row * size() + col;
            if (index < text_.size()) {
                result.push_back(text_[index]);
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string result = cipher_text();
    std::string normalized;
    for (std::size_t i = 0; i < result.size(); i += size()) {
        normalized += result.substr(i, size()) + " ";
    }
    return normalized;
}

}  // namespace crypto_square
