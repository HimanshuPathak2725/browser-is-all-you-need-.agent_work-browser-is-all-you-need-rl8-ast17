#include "crypto_square.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <vector>

namespace crypto_square {

cipher::cipher(std::string const& text) : text_(text) {}

std::string cipher::normalize_plain_text() const {
    std::string normalized;
    std::transform(text_.begin(), text_.end(), std::back_inserter(normalized),
                   [](char c) { return std::isalnum(c) ? std::tolower(c) : c; });
    normalized.erase(std::remove(normalized.begin(), normalized.end(), ' '),
                     normalized.end());
    return normalized;
}

std::size_t cipher::size() const {
    const std::string normalized = normalize_plain_text();
    if (normalized.empty()) return 0;
    return static_cast<std::size_t>(std::ceil(std::sqrt(normalized.size())));
}

std::vector<std::string> cipher::plain_text_segments() const {
    std::vector<std::string> segments;
    const std::string normalized = normalize_plain_text();
    for (std::size_t i = 0; i < normalized.size(); i += size()) {
        segments.push_back(normalized.substr(i, size()));
    }
    return segments;
}

std::string cipher::cipher_text() const {
    std::string result;
    for (const auto& segment : plain_text_segments()) {
        result += segment;
    }
    return result;
}

std::string cipher::normalized_cipher_text() const {
    std::string result;
    const std::vector<std::string> segments = plain_text_segments();
    for (std::size_t i = 0; i < segments.size(); ++i) {
        if (i != 0) result += ' ';
        result += segments[i];
    }
    return result;
}

}  // namespace crypto_square
