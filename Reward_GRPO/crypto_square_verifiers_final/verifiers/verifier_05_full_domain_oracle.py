from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_and_run, execute

from _contract import CONTRACT


POLICY_ID = "CSF-C05"
ORACLE_SUPPORT = r'''#include "crypto_square.h"
#include <cstddef>
#include <iostream>
#include <string>
#include <vector>
std::string normalize_ascii(const std::string& input) {
    std::string result;
    for (char byte : input) {
        if (byte >= 'A' && byte <= 'Z') result.push_back(static_cast<char>(byte - 'A' + 'a'));
        else if ((byte >= 'a' && byte <= 'z') || (byte >= '0' && byte <= '9')) result.push_back(byte);
    }
    return result;
}
std::size_t columns_for(std::size_t length) {
    std::size_t columns = 0;
    while (columns * columns < length) ++columns;
    return columns;
}
std::vector<std::string> segment_oracle(const std::string& normalized) {
    std::vector<std::string> result;
    const std::size_t columns = columns_for(normalized.size());
    if (columns == 0) return result;
    for (std::size_t offset = 0; offset < normalized.size(); offset += columns) {
        result.push_back(normalized.substr(offset, columns));
    }
    return result;
}
std::string cipher_oracle(const std::vector<std::string>& rows, std::size_t columns, bool padded) {
    std::string result;
    for (std::size_t column = 0; column < columns; ++column) {
        if (padded && column > 0) result.push_back(' ');
        for (const auto& row : rows) {
            if (column < row.size()) result.push_back(row.at(column));
            else if (padded) result.push_back(' ');
        }
    }
    return result;
}
bool exact(const std::string& input) {
    const std::string normalized = normalize_ascii(input);
    const std::size_t columns = columns_for(normalized.size());
    const auto segments = segment_oracle(normalized);
    const crypto_square::cipher value(input);
    return value.normalize_plain_text() == normalized
        && value.size() == columns
        && value.plain_text_segments() == segments
        && value.cipher_text() == cipher_oracle(segments, columns, false)
        && value.normalized_cipher_text() == cipher_oracle(segments, columns, true);
}
std::string generated_input(std::size_t length) {
    const std::string alphabet = "abcdefghijklmnopqrstuvwxyz0123456789";
    std::string input;
    for (std::size_t index = 0; index < length; ++index) {
        char byte = alphabet.at(index % alphabet.size());
        if (byte >= 'a' && byte <= 'z' && index % 3 == 0) byte = static_cast<char>(byte - 'a' + 'A');
        input.push_back(byte);
        if (index % 5 == 0) input += "!, ";
    }
    return input;
}
'''
FULL_ORACLE = ORACLE_SUPPORT + r'''
int main() {
    const std::vector<std::string> cases{
        "", "... --- ...", "A", "A b", "This is fun!", "Chill out.",
        "If man was meant to stay on the ground, god would have given us roots.",
        "A man, a plan, a canal: Panama!", "0123456789", "Mixed CASE and 123 punctuation!!!"
    };
    for (const auto& input : cases) if (!exact(input)) return 1;
    for (std::size_t length = 0; length <= 512; ++length) {
        if (!exact(generated_input(length))) return 2;
    }
    std::cout << "oracle-ok\n";
}
'''
INTERLEAVED = ORACLE_SUPPORT + r'''
int main() {
    const std::vector<std::string> sequence{
        generated_input(997), "", "Chill out.", generated_input(2),
        generated_input(255), "...", "This is fun!", generated_input(4096),
        "A man, a plan, a canal: Panama!"
    };
    std::vector<std::string> normalized;
    std::vector<std::string> ciphered;
    std::vector<std::string> padded;
    for (const auto& input : sequence) {
        const crypto_square::cipher value(input);
        normalized.push_back(value.normalize_plain_text());
        ciphered.push_back(value.cipher_text());
        padded.push_back(value.normalized_cipher_text());
        if (!exact(input)) return 1;
    }
    for (int round = 0; round < 4; ++round) {
        for (std::size_t reverse = sequence.size(); reverse > 0; --reverse) {
            const std::size_t index = reverse - 1;
            const crypto_square::cipher value(sequence.at(index));
            const crypto_square::cipher copied(value);
            if (!exact(sequence.at(index))) return 2;
            if (copied.normalize_plain_text() != normalized.at(index)) return 3;
            if (copied.cipher_text() != ciphered.at(index)) return 4;
            if (copied.normalized_cipher_text() != padded.at(index)) return 5;
        }
    }
    std::cout << "repeat-ok\n";
}
'''
SAFETY_FLAGS = ("-O1", "-D_GLIBCXX_ASSERTIONS", "-fsanitize=undefined", "-fno-sanitize-recover=undefined")


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_and_run(
            ctx,
            "CSF-C05-A",
            "full_ascii_and_length_oracle",
            "full_oracle.cpp",
            FULL_ORACLE,
            "oracle-ok\n",
            extra_flags=SAFETY_FLAGS,
        ),
        compile_and_run(
            ctx,
            "CSF-C05-B",
            "interleaved_repeat_copy_oracle",
            "repeat_oracle.cpp",
            INTERLEAVED,
            "repeat-ok\n",
            extra_flags=SAFETY_FLAGS,
        ),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
