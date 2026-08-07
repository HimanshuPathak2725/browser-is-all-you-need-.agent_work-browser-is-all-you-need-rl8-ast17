"""Owner source for the three CHARM V1 Crypto Square tasks."""

from __future__ import annotations

from scripts.charm_v1_topics.common import calibration_prompt, package, prompt, support


KEYED = r'''#pragma once
#include <algorithm>
#include <cmath>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>
namespace charm::cryptosquare {
inline bool keyed_ascii_alnum(unsigned char ch) {
    return (ch >= '0' && ch <= '9') || (ch >= 'A' && ch <= 'Z') ||
           (ch >= 'a' && ch <= 'z');
}
inline char keyed_ascii_lower(unsigned char ch) {
    return ch >= 'A' && ch <= 'Z'
        ? static_cast<char>(ch + ('a' - 'A'))
        : static_cast<char>(ch);
}
inline std::optional<std::string> encode_keyed(std::string_view input, const std::vector<std::size_t>& key) {
    std::string normalized;
    for (unsigned char ch : input) if (keyed_ascii_alnum(ch)) normalized.push_back(keyed_ascii_lower(ch));
    if (normalized.empty()) return key.empty() ? std::optional<std::string>("") : std::nullopt;
    std::size_t rows = static_cast<std::size_t>(std::sqrt(static_cast<long double>(normalized.size())));
    if (rows == 0) rows = 1;
    std::size_t columns = (normalized.size() + rows - 1) / rows;
    while (columns > rows + 1) { ++rows; columns = (normalized.size() + rows - 1) / rows; }
    if (key.size() != columns) return std::nullopt;
    std::vector<bool> seen(columns, false);
    for (std::size_t value : key) { if (value >= columns || seen[value]) return std::nullopt; seen[value] = true; }
    normalized.resize(rows * columns, 'x');
    std::string out;
    for (std::size_t row = 0; row < rows; ++row) {
        if (row != 0) out.push_back(' ');
        for (std::size_t destination = 0; destination < columns; ++destination)
            out.push_back(normalized[row * columns + key[destination]]);
    }
    return out;
}
}
'''
KEYED_TEST = r'''#include "keyed-square-transposition.h"
#include <cassert>
#include <optional>
#include <string>
#include <vector>
using charm::cryptosquare::encode_keyed;
int main() {
    assert(encode_keyed("", {}) == std::optional<std::string>(""));
    assert(!encode_keyed("", {0}));
    assert(encode_keyed("A b!12", {1, 0}) == std::optional<std::string>("ba 21"));
    assert(encode_keyed("abcdefghi", {2, 0, 1}) == std::optional<std::string>("cab fde igh"));
    assert(!encode_keyed("abcd", {0}));
    assert(!encode_keyed("abcd", {0, 0}));
    assert(!encode_keyed("abcd", {0, 2}));
    const std::string high_byte(1, static_cast<char>(0xE9));
    assert(encode_keyed(high_byte, {}) == std::optional<std::string>(""));
    return 0;
}
'''


STREAM = r'''#include <cmath>
#include <string>
#include <string_view>
#include <utility>
#include <vector>
namespace charm::cryptosquare {
inline bool streaming_ascii_alnum(unsigned char ch) {
    return (ch >= '0' && ch <= '9') || (ch >= 'A' && ch <= 'Z') ||
           (ch >= 'a' && ch <= 'z');
}
inline char streaming_ascii_lower(unsigned char ch) {
    return ch >= 'A' && ch <= 'Z'
        ? static_cast<char>(ch + ('a' - 'A'))
        : static_cast<char>(ch);
}
class StreamingEncoder {
public:
    bool append(std::string_view chunk) {
        if (done_) return false;
        for (unsigned char ch : chunk) if (streaming_ascii_alnum(ch)) text_.push_back(streaming_ascii_lower(ch));
        return true;
    }
    std::string finish() {
        if (done_) return result_;
        done_ = true;
        if (text_.empty()) return result_;
        const std::size_t columns = static_cast<std::size_t>(std::ceil(std::sqrt(static_cast<long double>(text_.size()))));
        const std::size_t rows = (text_.size() + columns - 1) / columns;
        for (std::size_t column = 0; column < columns; ++column) {
            if (column != 0) result_.push_back(' ');
            for (std::size_t row = 0; row < rows; ++row) {
                const std::size_t index = row * columns + column;
                result_.push_back(index < text_.size() ? text_[index] : ' ');
            }
        }
        return result_;
    }
    bool finished() const { return done_; }
private:
    std::string text_;
    std::string result_;
    bool done_ = false;
};
}
'''
STREAM_START = STREAM.replace("result_.push_back(index < text_.size() ? text_[index] : ' ');", "if (index < text_.size()) result_.push_back(text_[index]);")
STREAM_TEST = r'''#include "streaming-square-encoder.cpp"
#include <cassert>
#include <string>
using charm::cryptosquare::StreamingEncoder;
int main() {
    StreamingEncoder encoder;
    assert(!encoder.finished());
    assert(encoder.append("Ab!"));
    assert(encoder.append(" c12"));
    const std::string first = encoder.finish();
    assert(first == "a1 b2 c ");
    assert(encoder.finished() && encoder.finish() == first);
    assert(!encoder.append("ignored") && encoder.finish() == first);
    StreamingEncoder empty;
    assert(empty.finish().empty() && empty.finished());
    StreamingEncoder chunks;
    assert(chunks.append("a") && chunks.append("b") && chunks.finish() == "a b");
    StreamingEncoder ascii_only;
    assert(ascii_only.append(std::string(1, static_cast<char>(0xE9))));
    assert(ascii_only.finish().empty());
    return 0;
}
'''


DECODE = r'''#pragma once
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>
namespace charm::cryptosquare {
inline bool decoder_ascii_alnum(unsigned char ch) {
    return (ch >= '0' && ch <= '9') || (ch >= 'A' && ch <= 'Z') ||
           (ch >= 'a' && ch <= 'z');
}
inline bool decoder_ascii_space(unsigned char ch) {
    return ch == ' ' || ch == '\t' || ch == '\n' || ch == '\r' ||
           ch == '\f' || ch == '\v';
}
inline std::optional<std::string> decode_columns(std::string_view encoded) {
    std::vector<std::string> columns;
    std::size_t position = 0;
    while (position < encoded.size()) {
        while (position < encoded.size() &&
               decoder_ascii_space(static_cast<unsigned char>(encoded[position]))) ++position;
        if (position == encoded.size()) break;
        std::string column;
        while (position < encoded.size() &&
               !decoder_ascii_space(static_cast<unsigned char>(encoded[position]))) {
            column.push_back(encoded[position]);
            ++position;
        }
        columns.push_back(std::move(column));
    }
    if (columns.empty()) return std::string{};
    const std::size_t high = columns.front().size();
    if (high == 0) return std::nullopt;
    bool saw_short = false;
    for (const std::string& column : columns) {
        if (column.size() + 1 < high || column.size() > high) return std::nullopt;
        if (column.size() < high) saw_short = true;
        else if (saw_short) return std::nullopt;
        for (unsigned char ch : column) if (!decoder_ascii_alnum(ch)) return std::nullopt;
    }
    std::string out;
    for (std::size_t row = 0; row < high; ++row)
        for (const std::string& column : columns) if (row < column.size()) out.push_back(column[row]);
    return out;
}
}
'''
DECODE_TEST = r'''#include "ragged-square-decoder.hpp"
#include <cassert>
#include <optional>
#include <string>
using charm::cryptosquare::decode_columns;
int main() {
    assert(decode_columns("") == std::optional<std::string>(""));
    assert(decode_columns("ac bd") == std::optional<std::string>("abcd"));
    assert(decode_columns("adg beh cf") == std::optional<std::string>("abcdefgh"));
    assert(decode_columns("ad beh cf") == std::nullopt);
    assert(decode_columns("abc d") == std::nullopt);
    assert(decode_columns("ab c de") == std::nullopt);
    assert(decode_columns("ab c!") == std::nullopt);
    assert(decode_columns("ab  c") == std::optional<std::string>("acb"));
    const std::string high_byte(1, static_cast<char>(0xE9));
    assert(!decode_columns(high_byte));
    return 0;
}
'''


def tasks() -> list[dict]:
    keyed = ["keyed-square-transposition.h", "keyed-square-transposition.cpp"]
    stream = ["streaming-square-encoder.cpp"]
    decode = ["ragged-square-decoder.hpp"]
    keyed_prompt = calibration_prompt("Keyed square transposition", "Normalize ASCII alphanumerics to lowercase, form a near-square padded row grid, permute each row's columns by a validated key, and join rows with spaces. The key maps output column positions to source column indices.", "namespace charm::cryptosquare { std::optional<std::string> encode_keyed(std::string_view,const std::vector<std::size_t>&); }", ["empty normalized input requires an empty key", "padding uses lowercase x", "key length equals column count", "key is a complete permutation", "each output column reads the source column at the corresponding key entry", "punctuation is discarded"], keyed)
    rows = [
        package(topic="Crypto Square", task_id="charm-v1-keyed-square-transposition", instructions=keyed_prompt, editable={keyed[0]: KEYED, keyed[1]: support(keyed[0], 61)}, reference={keyed[0]: KEYED, keyed[1]: support(keyed[0], 61)}, hidden_name="keyed-square-transposition_test.cpp", hidden=KEYED_TEST, category="keyed-grid", tags=["calibration", "no-change", "permutation", "normalization"]),
        package(topic="Crypto Square", task_id="charm-v1-streaming-square-encoder", instructions=prompt("Streaming square encoder", "Accumulate ASCII-alphanumeric chunks normalized to lowercase, choose rectangular dimensions only on the first finish, emit space-separated padded columns, and make finish idempotent.", "namespace charm::cryptosquare { class StreamingEncoder { public: bool append(std::string_view); std::string finish(); bool finished() const; }; }", ["punctuation is ignored", "empty finish", "padding preserves a rectangle", "append after finish rejects", "repeated finish is byte-identical"], stream), editable={stream[0]: STREAM_START}, reference={stream[0]: STREAM}, hidden_name="streaming-square-encoder_test.cpp", hidden=STREAM_TEST, category="streaming-finalization", tags=["partial", "state-machine", "idempotence", "cpp-only"]),
        package(topic="Crypto Square", task_id="charm-v1-ragged-square-decoder", instructions=prompt("Ragged square decoder", "Decode whitespace-separated columns of ASCII alphanumerics row-wise, accepting only the legal long-columns-first height pattern and rejecting malformed symbols.", "namespace charm::cryptosquare { std::optional<std::string> decode_columns(std::string_view); }", ["empty input decodes empty", "column heights differ by at most one", "long columns precede short columns", "non-alphanumeric column data rejects", "multiple whitespace separators are allowed"], decode), editable={decode[0]: "#pragma once\nnamespace charm::cryptosquare {}\n"}, reference={decode[0]: DECODE}, hidden_name="ragged-square-decoder_test.cpp", hidden=DECODE_TEST, category="ragged-decoding", tags=["header-only", "shape-validation", "decoder", "optional"]),
    ]
    for row in rows:
        row["release_version"] = "v002"
    return rows
