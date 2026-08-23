#pragma once

#include <cstddef>
#include <string>
#include <vector>

namespace crypto_square {

class cipher {
public:
    explicit cipher(std::string const& text);
    std::string normalize_plain_text() const;
    std::size_t size() const;
    std::vector<std::string> plain_text_segments() const;
    std::string cipher_text() const;
    std::string normalized_cipher_text() const;

private:
    std::string text_;
    mutable std::size_t cols_ = 0;
    mutable std::size_t rows_ = 0;

    void calculate_dimensions() const;
};

}  // namespace crypto_square
