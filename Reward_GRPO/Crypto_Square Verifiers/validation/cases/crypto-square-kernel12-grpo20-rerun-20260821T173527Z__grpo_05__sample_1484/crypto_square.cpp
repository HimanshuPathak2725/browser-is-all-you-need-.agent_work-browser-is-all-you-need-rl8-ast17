#include "crypto_square.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <vector>

namespace crypto_square {

cipher::cipher(std::string const& text) : text_(text) {}

std::string cipher::normalize_plain_text() const {
    std::string result;
    result.reserve(text_.size());
    for (char c : text_) {
        if (std::isalnum(static_cast<unsigned char>(c))) {
            result += static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
        }
    }
    return result;
}

std::size_t cipher::size() const {
    std::string normalized = normalize_plain_text();
    std::size_t len = normalized.size();
    return len == 0 ? 0 : static_cast<std::size_t>(std::ceil(std::sqrt(len)));
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::string normalized = normalize_plain_text();
    std::size_t seg_size = size();
    std::vector<std::string> segments;
    for (std::size_t i = 0; i < normalized.size(); i += seg_size) {
        segments.push_back(normalized.substr(i, seg_size));
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string normalized = normalize_plain_text();
    std::size_t cols = size();
    if (cols == 0) {
        return "";
    }
    std::size_t rows = (normalized.size() + cols - 1) / cols;
    std::string result;
    result.reserve(normalized.size());
    for (std::size_t c = 0; c < cols; ++c) {
        for (std::size_t r = 0; r < rows; ++r) {
            std::size_t index = r * cols + c;
            if (index < normalized.size()) {
                result += normalized[index];
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string normalized = normalize_plain_text();
    std::size_t cols = size();
    if (cols == 0) {
        return "";
    }
    std::size_t rows = (normalized.size() + cols - 1) / cols;
    std::vector<std::string> segments;
    for (std::size_t c = 0; c < cols; ++c) {
        std::string segment;
        segment.reserve(cols);
        for (std::size_t r = 0; r < rows; ++r) {
            std::size_t index = r * cols + c;
            if (index < normalized.size()) {
                segment += normalized[index];
            } else {
                segment += ' ';
            }
        }
        segments.push_back(segment);
    }
    std::string result;
    result.reserve(normalized.size() + segments.size());
    for (std::size_t i = 0; i < segments.size(); ++i) {
        result += segments[i];
        if (i != segments.size() - 1) {
            result += ' ';
        }
    }
    return result;
}

}  // namespace crypto_square
