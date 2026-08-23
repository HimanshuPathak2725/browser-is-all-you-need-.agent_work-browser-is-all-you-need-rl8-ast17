#include "crypto_square.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <sstream>
#include <vector>

namespace crypto_square {

cipher::cipher(std::string const& text) : text_(text) {}

std::string cipher::normalize_plain_text() const {
    std::string normalized;
    for (const char c : text_) {
        if (std::isalnum(static_cast<unsigned char>(c))) {
            normalized += std::tolower(static_cast<unsigned char>(c));
        }
    }
    return normalized;
}

std::size_t cipher::size() const {
    std::size_t len = normalize_plain_text().size();
    return static_cast<std::size_t>(std::ceil(std::sqrt(len)));
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::string normalized = normalize_plain_text();
    std::vector<std::string> result;
    std::size_t segment_size = size();

    for (std::size_t i = 0; i < normalized.size(); i += segment_size) {
        result.push_back(normalized.substr(i, segment_size));
    }
    return result;
}

std::string cipher::cipher_text() const {
    std::string result;
    std::vector<std::string> segments = plain_text_segments();
    for (std::size_t col = 0; col < segments[0].size(); ++col) {
        for (std::size_t row = 0; row < segments.size(); ++row) {
            if (col < segments[row].size()) {
                result += segments[row][col];
            }
        }
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string result;
    std::vector<std::string> segments = plain_text_segments();
    for (std::size_t col = 0; col < segments[0].size(); ++col) {
        for (std::size_t row = 0; row < segments.size(); ++row) {
            if (col < segments[row].size()) {
                result += segments[row][col];
            }
        }
        if (col < segments[0].size() - 1) {
            result += ' ';
        }
    }
    return result;
}

}  // namespace crypto_square
