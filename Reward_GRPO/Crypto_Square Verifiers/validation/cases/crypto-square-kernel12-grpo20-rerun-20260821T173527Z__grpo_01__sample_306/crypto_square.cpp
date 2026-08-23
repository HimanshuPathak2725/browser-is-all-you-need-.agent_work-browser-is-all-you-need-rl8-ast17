#include "crypto_square.h"

#include <cctype>
#include <cmath>
#include <sstream>
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
    if (text_.empty()) return 0;
    return static_cast<std::size_t>(std::ceil(std::sqrt(text_.size())));
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::vector<std::string> segments;
    if (text_.empty()) return segments;

    const std::size_t segment_size = size();
    for (std::size_t start = 0; start < text_.size(); start += segment_size) {
        std::string segment = text_.substr(start, segment_size);
        if (segment.size() < segment_size) {
            segment.append(segment_size - segment.size(), ' ');
        }
        segments.push_back(segment);
    }
    return segments;
}

std::string cipher::cipher_text() const {
    if (text_.empty()) return "";

    std::string result;
    const std::size_t n = size();
    for (std::size_t col = 0; col < n; ++col) {
        for (std::size_t row = 0; row < n; ++row) {
            const std::size_t index = col + row * n;
            if (index < text_.size()) {
                result.push_back(text_[index]);
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    const std::string cipher = cipher_text();
    if (cipher.empty()) return "";

    std::vector<std::string> segments;
    const std::size_t n = size();
    for (std::size_t start = 0; start < cipher.size(); start += n) {
        segments.push_back(cipher.substr(start, n));
    }

    std::ostringstream result;
    for (const std::string& segment : segments) {
        result << segment << ' ';
    }
    return result.str();
}

}  // namespace crypto_square
