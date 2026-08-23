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
    std::vector<std::string> segments;
    for (std::size_t i = 0; i < text_.size(); i += size()) {
        segments.push_back(text_.substr(i, size()));
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string result;
    for (std::size_t i = 0; i < size(); ++i) {
        for (std::size_t j = 0; j < text_.size(); j += size()) {
            if (i + j < text_.size()) {
                result += text_[i + j];
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string result;
    for (std::size_t i = 0; i < size(); ++i) {
        std::string col;
        for (std::size_t j = 0; j < text_.size(); j += size()) {
            if (i + j < text_.size()) {
                col += text_[i + j];
            } else {
                col += ' ';
            }
        }
        result += col + " ";
    }
    return result.substr(0, result.size() - 1);
}

}  // namespace crypto_square
