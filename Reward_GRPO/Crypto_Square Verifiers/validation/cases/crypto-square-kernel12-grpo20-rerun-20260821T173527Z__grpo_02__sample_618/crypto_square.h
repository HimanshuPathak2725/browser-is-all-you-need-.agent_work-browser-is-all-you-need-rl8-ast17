#pragma once

#include <string>
#include <vector>

namespace crypto_square {

class cipher {
public:
    cipher(std::string const& text);
    std::string normalize_plain_text() const;
    std::size_t size() const;
    std::vector<std::string> plain_text_segments() const;
    std::string cipher_text() const;
    std::string normalized_cipher_text() const;

private:
    std::string normalized_;
    std::string text_;
    std::size_t size_;
};

}  // namespace crypto_square
