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
    std::vector<std::string> rows;
    const std::size_t columns = size();
    if (columns == 0) return rows;
    for (std::size_t offset = 0; offset < text_.size(); offset += columns) {
        rows.push_back(text_.substr(offset, columns));
    }
    return rows;
}

std::string cipher::cipher_text() const {
    std::string output;
    const auto rows = plain_text_segments();
    for (std::size_t column = 0; column < size(); ++column) {
        for (const auto& row : rows) {
            if (column < row.size()) output.push_back(row[column]);
        }
    }
    return output;
}

std::string cipher::normalized_cipher_text() const {
    if (text_.empty()) return "";
    const std::size_t cols = size();
    std::string output;

    for (std::size_t column = 0; column < cols; ++column) {
        if (column != 0) output.push_back(' ');
        std::string segment;
        for (std::size_t row = 0; row < text_.size(); row += cols) {
            const std::size_t index = row + column;
            if (index < text_.size()) {
                segment.push_back(text_[index]);
            } else {
                segment.push_back(' ');
            }
        }
        output += segment;
    }
    return output;
}

}  // namespace crypto_square
