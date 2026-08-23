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

std::string cipher::cipher_text() const {
    std::string result;
    for (std::size_t c = 0; c < size(); ++c) {
        for (std::size_t r = 0; r < size(); ++r) {
            std::size_t index = r * size() + c;
            if (index < text_.size()) {
                result.push_back(text_[index]);
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string result;
    for (std::size_t c = 0; c < size(); ++c) {
        for (std::size_t r = 0; r < size(); ++r) {
            std::size_t index = r * size() + c;
            if (index < text_.size()) {
                result.push_back(text_[index]);
            } else {
                result.push_back(' ');
            }
        }
        if (c != size() - 1) {
            result.push_back(' ');
        }
    }
    return result;
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::vector<std::string> result;
    for (std::size_t r = 0; r < size(); ++r) {
        std::string segment;
        for (std::size_t c = 0; c < size(); ++c) {
            std::size_t index = r * size() + c;
            if (index < text_.size()) {
                segment.push_back(text_[index]);
            } else {
                segment.push_back(' ');
            }
        }
        result.push_back(segment);
    }
    return result;
}

}  // namespace crypto_square
