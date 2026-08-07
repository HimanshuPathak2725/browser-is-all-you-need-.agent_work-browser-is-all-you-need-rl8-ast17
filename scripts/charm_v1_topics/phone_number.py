"""Owner source for the three CHARM V1 Phone Number tasks."""

from __future__ import annotations

from scripts.charm_v1_topics.common import package, prompt, support


CANONICAL = r'''#pragma once
#include <optional>
#include <string>
#include <string_view>
namespace charm::phone {
inline bool canonical_ascii_digit(unsigned char ch) {
    return ch >= '0' && ch <= '9';
}
inline bool canonical_ascii_alpha(unsigned char ch) {
    return (ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z');
}
inline bool canonical_ascii_space(unsigned char ch) {
    return ch == ' ' || ch == '\t' || ch == '\n' || ch == '\r' ||
           ch == '\f' || ch == '\v';
}
inline char canonical_ascii_lower(unsigned char ch) {
    return ch >= 'A' && ch <= 'Z'
        ? static_cast<char>(ch + ('a' - 'A'))
        : static_cast<char>(ch);
}
struct CanonicalPhone { std::string number; std::string extension; };
inline std::optional<CanonicalPhone> canonicalize(std::string_view input) {
    std::string main_part(input);
    std::string extension;
    std::size_t marker = std::string::npos;
    std::size_t marker_length = 0;
    for (std::size_t i = 0; i < main_part.size(); ++i) {
        if (main_part[i] == 'x' || main_part[i] == 'X') {
            marker = i;
            marker_length = 1;
            break;
        }
        if (i + 3 <= main_part.size() &&
            canonical_ascii_lower(static_cast<unsigned char>(main_part[i])) == 'e' &&
            canonical_ascii_lower(static_cast<unsigned char>(main_part[i + 1])) == 'x' &&
            canonical_ascii_lower(static_cast<unsigned char>(main_part[i + 2])) == 't') {
            marker = i;
            marker_length = 3;
            break;
        }
    }
    if (marker != std::string::npos) {
        std::size_t position = marker + marker_length;
        while (position < main_part.size()) {
            const unsigned char ch = main_part[position];
            if (!canonical_ascii_space(ch) && ch != '.' && ch != '-') break;
            ++position;
        }
        if (position == main_part.size() ||
            !canonical_ascii_digit(static_cast<unsigned char>(main_part[position]))) {
            return std::nullopt;
        }
        for (; position < main_part.size(); ++position) {
            const unsigned char ch = main_part[position];
            if (canonical_ascii_digit(ch)) extension.push_back(static_cast<char>(ch));
            else if (!canonical_ascii_space(ch) && ch != '.' && ch != '-') return std::nullopt;
        }
        if (extension.empty() || extension.size() > 6) return std::nullopt;
        main_part.resize(marker);
    }
    std::string digits;
    bool leading_plus = false;
    for (std::size_t index = 0; index < main_part.size(); ++index) {
        const unsigned char ch = main_part[index];
        if (canonical_ascii_digit(ch)) digits.push_back(static_cast<char>(ch));
        else if (canonical_ascii_alpha(ch)) return std::nullopt;
        else if (ch == '+') {
            if (index != 0 || leading_plus) return std::nullopt;
            leading_plus = true;
        } else if (!canonical_ascii_space(ch) && ch != '-' && ch != '(' &&
                   ch != ')' && ch != '.') {
            return std::nullopt;
        }
    }
    if (leading_plus) {
        if (digits.size() != 11 || digits.front() != '1') return std::nullopt;
        digits.erase(digits.begin());
    } else if (digits.size() == 11 && digits.front() == '1') {
        digits.erase(digits.begin());
    }
    if (digits.size() != 10 || digits[0] < '2' || digits[0] > '9' ||
        digits[3] < '2' || digits[3] > '9') return std::nullopt;
    return CanonicalPhone{digits, extension};
}
}
'''
CANONICAL_START = r'''#pragma once
#include <optional>
#include <string>
#include <string_view>
namespace charm::phone {
struct CanonicalPhone { std::string number; std::string extension; };
std::optional<CanonicalPhone> canonicalize(string_view input);
}
'''
CANONICAL_TEST = r'''#include "extension-canonicalizer.h"
#include <cassert>
using charm::phone::canonicalize;
int main() {
    const auto plain = canonicalize("(212) 555-0123");
    assert(plain && plain->number == "2125550123" && plain->extension.empty());
    const auto country = canonicalize("+1 212 555 0123 x45");
    assert(country && country->number == "2125550123" && country->extension == "45");
    const auto ext = canonicalize("415.555.9999 ext. 007");
    assert(ext && ext->extension == "007");
    assert(!canonicalize("1125550123"));
    assert(!canonicalize("2121550123"));
    assert(!canonicalize("212CALLNOW"));
    assert(!canonicalize("2125550123 x"));
    assert(!canonicalize("2125550123 x1234567"));
    assert(!canonicalize("234+5678901"));
    assert(!canonicalize("+2125550123"));
    assert(!canonicalize("2125550123 ext junk 5"));
    assert(!canonicalize(std::string("2125550123") + static_cast<char>(0xE9)));
    return 0;
}
'''


DIAL = r'''#include <map>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
namespace charm::phone {
class DialPlan {
public:
    bool add(std::string prefix, std::string route_name) {
        if (prefix.empty() || route_name.empty()) return false;
        for (unsigned char ch : prefix) if (ch < '0' || ch > '9') return false;
        return routes_.emplace(std::move(prefix), std::move(route_name)).second;
    }
    std::optional<std::pair<std::string,std::string>> route(std::string_view digits) const {
        for (unsigned char ch : digits) if (ch < '0' || ch > '9') return std::nullopt;
        const std::pair<const std::string,std::string>* best = nullptr;
        for (const auto& item : routes_) if (digits.substr(0, item.first.size()) == item.first && (!best || item.first.size() > best->first.size())) best = &item;
        if (!best) return std::nullopt;
        return std::pair<std::string,std::string>{best->second, std::string(digits.substr(best->first.size()))};
    }
private:
    std::map<std::string,std::string> routes_;
};
}
'''
DIAL_START = DIAL.replace("item.first.size() > best->first.size()", "item.first.size() < best->first.size()")
DIAL_TEST = r'''#include "dial-plan-router.cpp"
#include <cassert>
#include <string>
#include <utility>
using charm::phone::DialPlan;
int main() {
    DialPlan plan;
    assert(!plan.add("", "root") && !plan.add("12a", "bad") && !plan.add("12", ""));
    assert(plan.add("1", "country") && plan.add("1212", "city") && plan.add("1212555", "exchange"));
    assert(!plan.add("1", "duplicate"));
    assert(plan.route("12125550123") == std::make_optional(std::make_pair(std::string("exchange"), std::string("0123"))));
    assert(plan.route("199") == std::make_optional(std::make_pair(std::string("country"), std::string("99"))));
    assert(!plan.route("999") && !plan.route("12x"));
    assert(plan.route("1212") == std::make_optional(std::make_pair(std::string("city"), std::string(""))));
    return 0;
}
'''


VANITY = r'''#pragma once
#include <optional>
#include <string>
#include <string_view>
namespace charm::phone {
inline bool vanity_ascii_digit(unsigned char ch) {
    return ch >= '0' && ch <= '9';
}
inline bool vanity_ascii_alpha(unsigned char ch) {
    return (ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z');
}
inline bool vanity_ascii_space(unsigned char ch) {
    return ch == ' ' || ch == '\t' || ch == '\n' || ch == '\r' ||
           ch == '\f' || ch == '\v';
}
inline char vanity_ascii_upper(unsigned char ch) {
    return ch >= 'a' && ch <= 'z'
        ? static_cast<char>(ch - ('a' - 'A'))
        : static_cast<char>(ch);
}
inline std::optional<std::string> normalize_vanity(std::string_view input) {
    std::string digits;
    bool leading_plus = false;
    for (std::size_t index = 0; index < input.size(); ++index) {
        const unsigned char raw = input[index];
        if (raw == '+') {
            if (index != 0 || leading_plus) return std::nullopt;
            leading_plus = true;
            continue;
        }
        if (vanity_ascii_digit(raw)) {
            digits.push_back(static_cast<char>(raw));
            continue;
        }
        if (vanity_ascii_alpha(raw)) {
            const char ch = vanity_ascii_upper(raw);
            const char mapped =
                ch <= 'C' ? '2' : ch <= 'F' ? '3' : ch <= 'I' ? '4' :
                ch <= 'L' ? '5' : ch <= 'O' ? '6' : ch <= 'S' ? '7' :
                ch <= 'V' ? '8' : '9';
            digits.push_back(mapped);
            continue;
        }
        if (!vanity_ascii_space(raw) && raw != '-' && raw != '(' &&
            raw != ')' && raw != '.') return std::nullopt;
    }
    if (digits.size() != 10 && digits.size() != 11) return std::nullopt;
    if (leading_plus && digits.size() != 11) return std::nullopt;
    return (leading_plus ? "+" : "") + digits;
}
}
'''
VANITY_TEST = r'''#include "vanity-number-repair.h"
#include <cassert>
#include <optional>
#include <string>
using charm::phone::normalize_vanity;
int main() {
    assert(normalize_vanity("1-800-FLOWERS") == std::optional<std::string>("18003569377"));
    assert(normalize_vanity("212-PAINTER") == std::optional<std::string>("2127246837"));
    assert(normalize_vanity("+1 (800) FLOWERS") == std::optional<std::string>("+18003569377"));
    assert(!normalize_vanity("+212-PAINTER"));
    assert(!normalize_vanity("21+2PAINTER"));
    assert(!normalize_vanity("CALL"));
    assert(!normalize_vanity("212_PAINTER"));
    assert(normalize_vanity("9999999999") == std::optional<std::string>("9999999999"));
    assert(!normalize_vanity(std::string("212PAINTER") + static_cast<char>(0xE9)));
    return 0;
}
'''


def tasks() -> list[dict]:
    canonical = ["extension-canonicalizer.h", "extension-canonicalizer.cpp"]
    dial = ["dial-plan-router.cpp"]
    vanity = ["vanity-number-repair.h", "vanity-number-repair.cpp"]
    return [
        package(topic="Phone Number", task_id="charm-v1-extension-canonicalizer", instructions=prompt("Extension canonicalizer", "Canonicalize a North-American ten-digit number with an optional leading +1/1 country code and optional x/ext extension. Only ASCII digits, ASCII whitespace, and the listed separators are accepted; extension markers may be followed only by separators and 1..6 digits.", "namespace charm::phone { struct CanonicalPhone { std::string number; std::string extension; }; std::optional<CanonicalPhone> canonicalize(std::string_view); }", ["optional leading country code 1", "area and exchange begin 2..9", "extension is 1..6 digits", "letters before extension reject", "unsupported punctuation rejects"], canonical), editable={canonical[0]: CANONICAL_START, canonical[1]: support(canonical[0], 121)}, reference={canonical[0]: CANONICAL, canonical[1]: support(canonical[0], 122)}, hidden_name="extension-canonicalizer_test.cpp", hidden=CANONICAL_TEST, category="number-extension", tags=["compile-repair", "canonicalization", "public-api", "validation"]),
        package(topic="Phone Number", task_id="charm-v1-dial-plan-router", instructions=prompt("Dial plan router", "Store unique digit prefixes and choose the longest prefix of a digit-only dial string, returning route name and unmatched subscriber digits.", "namespace charm::phone { class DialPlan { public: bool add(std::string,std::string); std::optional<std::pair<std::string,std::string>> route(std::string_view) const; }; }", ["empty or nondigit prefixes reject", "duplicate prefix rejects", "nondigit dial string rejects", "longest prefix wins", "subscriber suffix may be empty"], dial), editable={dial[0]: DIAL_START}, reference={dial[0]: DIAL}, hidden_name="dial-plan-router_test.cpp", hidden=DIAL_TEST, category="longest-prefix", tags=["linker-repair", "prefix", "routing", "cpp-only"]),
        package(topic="Phone Number", task_id="charm-v1-vanity-number-repair", instructions=prompt("Vanity number repair", "Normalize ASCII classic-keypad letters and digits while ignoring conventional ASCII separators; preserve a leading plus only for an eleven-digit result.", "namespace charm::phone { std::optional<std::string> normalize_vanity(std::string_view); }", ["letters map case-insensitively", "plus is only allowed first", "leading plus requires eleven digits", "plain results contain ten or eleven digits", "unknown separators reject"], vanity), editable={vanity[0]: "#pragma once\nnamespace charm::phone {}\n", vanity[1]: support(vanity[0], 123)}, reference={vanity[0]: VANITY, vanity[1]: support(vanity[0], 124)}, hidden_name="vanity-number-repair_test.cpp", hidden=VANITY_TEST, category="vanity-normalization", tags=["header-reconstruction", "keypad", "optional-plus", "repair"]),
    ]
