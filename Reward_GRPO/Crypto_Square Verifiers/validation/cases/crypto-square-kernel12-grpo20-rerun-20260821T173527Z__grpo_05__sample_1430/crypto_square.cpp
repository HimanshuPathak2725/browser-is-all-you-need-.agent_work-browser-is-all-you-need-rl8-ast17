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
    std::vector<std::string> segments = plain_text_segments();
    for (std::size_t col = 0; col < size(); ++col) {
        for (std::size_t row = 0; row < segments.size(); ++row) {
            if (col < segments[row].size()) {
                result += segments[row][col];
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::vector<std::string> segments = plain_text_segments();
    std::size_t max_len = 0;
    for (const auto& segment : segments) {
        if (segment.size() > max_len) max_len = segment.size();
    }

    for (auto& segment : segments) {
        while (segment.size() < max_len) segment += ' ';
    }

    std::string result;
    for (std::size_t col = 0; col < max_len; ++col) {
        for (std::size_t row = 0; row < segments.size(); ++row) {
            result += segments[row][col];
        }
        if (col != max_len - 1) result += ' ';
    }
    return result;
}

}  // namespace crypto_square
