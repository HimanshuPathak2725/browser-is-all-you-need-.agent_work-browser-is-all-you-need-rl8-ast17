# Policy 6 verifier: decompose compact transposition, geometry, and exact padding.
from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, execute
from strange_cpp_semantic import compile_and_run

from _contract import CONTRACT


POLICY_ID = "CS-E06"
PROBE = r'''#include "crypto_square.h"
#include <array>
#include <cctype>
#include <iostream>
#include <string>
#include <vector>

std::string normalize(const std::string& input) {
    std::string output;
    for (const unsigned char character : input) {
        if (std::isalnum(character)) output.push_back(static_cast<char>(std::tolower(character)));
    }
    return output;
}

std::size_t columns(std::size_t length) {
    std::size_t result = 0;
    while (result * result < length) ++result;
    return result;
}

std::vector<std::string> segments(const std::string& input) {
    const std::string normalized = normalize(input);
    const std::size_t width = columns(normalized.size());
    std::vector<std::string> rows;
    if (width == 0) return rows;
    for (std::size_t offset = 0; offset < normalized.size(); offset += width) {
        rows.push_back(normalized.substr(offset, width));
    }
    return rows;
}

std::string compact(const std::string& input) {
    const auto rows = segments(input);
    const std::size_t width = columns(normalize(input).size());
    std::string output;
    for (std::size_t column = 0; column < width; ++column) {
        for (const auto& row : rows) if (column < row.size()) output.push_back(row[column]);
    }
    return output;
}

std::string formatted(const std::string& input) {
    const auto rows = segments(input);
    const std::size_t width = columns(normalize(input).size());
    if (width == 0) return "";
    std::string output;
    for (std::size_t column = 0; column < width; ++column) {
        if (column != 0) output.push_back(' ');
        for (const auto& row : rows) output.push_back(column < row.size() ? row[column] : ' ');
    }
    return output;
}

bool geometry(const std::string& input) {
    const std::string normalized = normalize(input);
    const std::size_t width = columns(normalized.size());
    const std::string output = crypto_square::cipher(input).normalized_cipher_text();
    if (width == 0) return output.empty();
    const std::size_t height = (normalized.size() + width - 1) / width;
    if (output.size() != width * height + width - 1) return false;
    std::size_t cursor = 0;
    for (std::size_t column = 0; column < width; ++column) {
        cursor += height;
        if (column + 1 < width) {
            if (output[cursor] != ' ') return false;
            ++cursor;
        }
    }
    return cursor == output.size();
}

int main(int argc, char** argv) {
    if (argc != 2) return 90;
    const std::string group(argv[1]);
    if (group == "compact_transpose") {
        if (crypto_square::cipher("This is fun!").cipher_text() != "tsfhiuisn") return 1;
        if (crypto_square::cipher("Chill out.").cipher_text() != "cluhltio") return 2;
        if (crypto_square::cipher("If man was meant to stay on the ground, god would have given us roots.").cipher_text() !=
            "imtgdvsfearwermayoogoanouuiontnnlvtwttddesaohghnsseoau") return 3;
    } else if (group == "chunk_geometry") {
        for (const std::string& input : {std::string("A"), std::string("ab"), std::string("abcde"),
             std::string("Chill out."), std::string("1234567890"),
             std::string("If man was meant to stay on the ground, god would have given us roots.")}) {
            if (!geometry(input)) return 4;
        }
    } else if (group == "exact_padding") {
        const std::array<std::string, 6> inputs{
            "ab", "abcde", "Chill out.", "1234567890", "This is fun!",
            "If man was meant to stay on the ground, god would have given us roots."};
        for (const auto& input : inputs) {
            const crypto_square::cipher value(input);
            if (value.cipher_text() != compact(input) || value.normalized_cipher_text() != formatted(input)) return 5;
        }
    } else return 91;
    std::cout << "ok:" << group << '\n';
}
'''


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_and_run(ctx, "CS-E06-A", "compact_transpose", "layout_compact_transpose.cpp", PROBE, "ok:compact_transpose\n"),
        compile_and_run(ctx, "CS-E06-B", "chunk_geometry", "layout_chunk_geometry.cpp", PROBE, "ok:chunk_geometry\n"),
        compile_and_run(ctx, "CS-E06-C", "exact_padding", "layout_exact_padding.cpp", PROBE, "ok:exact_padding\n"),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
