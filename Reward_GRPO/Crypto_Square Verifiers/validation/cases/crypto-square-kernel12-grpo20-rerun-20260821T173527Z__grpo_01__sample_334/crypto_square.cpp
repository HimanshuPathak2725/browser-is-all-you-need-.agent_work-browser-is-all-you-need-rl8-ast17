#include "crypto_square.h"

#include <algorithm>
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
    const std::size_t segment_size = size();
    for (std::size_t start = 0; start < text_.size(); start += segment_size) {
        std::size_t end = std::min(start + segment_size, text_.size());
        std::string segment = text_.substr(start, end - start);
        while (segment.size() < segment_size) {
            segment.push_back(' ');
        }
        segments.push_back(segment);
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string cipher;
    const std::size_t segment_size = size();
    for (std::size_t col = 0; col < segment_size; ++col) {
        for (std::size_t row = 0; row < segment_size; ++row) {
            const std::size_t index = row * segment_size + col;
            if (index < text_.size()) {
                cipher.push_back(text_[index]);
            } else {
                cipher.push_back(' ');
            }
        }
    }
    return cipher;
}

std::string cipher::normalized_cipher_text() const {
    std::string cipher = cipher_text();
    std::vector<std::string> segments;
    const std::size_t segment_size = size();
    for (std::size_t start = 0; start < cipher.size(); start += segment_size) {
        std::size_t end = std::min(start + segment_size, cipher.size());
        segments.push_back(cipher.substr(start, end - start));
    }
    std::string result;
    for (std::size_t i = 0; i < segments.size(); ++i) {
        if (i != 0) result.push_back(' ');
        result += segments[i];
    }
    return result;
}

}  // namespace crypto_square
