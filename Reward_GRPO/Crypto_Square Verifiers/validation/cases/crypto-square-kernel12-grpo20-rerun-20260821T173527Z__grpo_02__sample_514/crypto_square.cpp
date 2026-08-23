#include "crypto_square.h"

#include <cctype>
#include <cmath>
#include <numeric>

namespace crypto_square {

cipher::cipher(std::string const& text) : text_(text) {}

std::string cipher::normalize_plain_text() const {
    std::string normalized;
    normalized.reserve(text_.size());
    for (const char c : text_) {
        if (std::isalnum(static_cast<unsigned char>(c))) {
            normalized.push_back(std::tolower(static_cast<unsigned char>(c)));
        }
    }
    return normalized;
}

std::size_t cipher::size() const {
    return normalize_plain_text().size();
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::string const& normalized = normalize_plain_text();
    std::vector<std::string> segments;
    
    std::size_t const n = normalized.size();
    if (n == 0) {
        return segments;
    }
    
    std::size_t cols = static_cast<std::size_t>(std::ceil(std::sqrt(n)));
    std::size_t rows = static_cast<std::size_t>(std::floor(std::sqrt(n)));
    
    if (cols < rows) {
        std::swap(cols, rows);
    }
    
    for (std::size_t row = 0; row < rows; ++row) {
        std::size_t start = row * cols;
        std::size_t end = std::min(start + cols, n);
        segments.push_back(normalized.substr(start, end - start));
    }
    
    return segments;
}

std::string cipher::cipher_text() const {
    std::string const& normalized = normalize_plain_text();
    std::string result;
    result.reserve(normalized.size());
    
    std::size_t const n = normalized.size();
    if (n == 0) {
        return result;
    }
    
    std::size_t cols = static_cast<std::size_t>(std::ceil(std::sqrt(n)));
    std::size_t rows = static_cast<std::size_t>(std::floor(std::sqrt(n)));
    
    if (cols < rows) {
        std::swap(cols, rows);
    }
    
    for (std::size_t col = 0; col < cols; ++col) {
        for (std::size_t row = 0; row < rows; ++row) {
            std::size_t index = row * cols + col;
            if (index < n) {
                result.push_back(normalized[index]);
            }
        }
    }
    
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string const& normalized = normalize_plain_text();
    std::string result;
    result.reserve(normalized.size());
    
    std::size_t const n = normalized.size();
    if (n == 0) {
        return result;
    }
    
    std::size_t cols = static_cast<std::size_t>(std::ceil(std::sqrt(n)));
    std::size_t rows = static_cast<std::size_t>(std::floor(std::sqrt(n)));
    
    if (cols < rows) {
        std::swap(cols, rows);
    }
    
    for (std::size_t col = 0; col < cols; ++col) {
        for (std::size_t row = 0; row < rows; ++row) {
            std::size_t index = row * cols + col;
            if (index < n) {
                result.push_back(normalized[index]);
            }
        }
        if (col < cols - 1) {
            result.push_back(' ');
        }
    }
    
    return result;
}

}  // namespace crypto_square
