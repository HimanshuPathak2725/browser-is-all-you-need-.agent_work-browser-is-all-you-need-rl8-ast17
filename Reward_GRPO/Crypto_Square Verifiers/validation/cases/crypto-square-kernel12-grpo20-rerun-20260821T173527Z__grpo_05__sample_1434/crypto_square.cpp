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
    std::vector<std::string> result;
    std::size_t segment_len = size();
    for (std::size_t i = 0; i < text_.size(); i += segment_len) {
        std::string segment = text_.substr(i, segment_len);
        while (segment.size() < segment_len) segment.push_back(' ');
        result.push_back(segment);
    }
    return result;
}

std::string cipher::cipher_text() const {
    std::string result;
    std::size_t segment_len = size();
    for (std::size_t col = 0; col < segment_len; ++col) {
        for (auto const& segment : plain_text_segments()) {
            if (col < segment.size()) result += segment[col];
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string result;
    std::size_t segment_len = size();
    for (std::size_t col = 0; col < segment_len; ++col) {
        std::string segment;
        for (auto const& plain_segment : plain_text_segments()) {
            if (col < plain_segment.size()) segment += plain_segment[col];
        }
        result += segment + " ";
    }
    if (!result.empty()) result.pop_back();
    return result;
}

}  // namespace crypto_square
