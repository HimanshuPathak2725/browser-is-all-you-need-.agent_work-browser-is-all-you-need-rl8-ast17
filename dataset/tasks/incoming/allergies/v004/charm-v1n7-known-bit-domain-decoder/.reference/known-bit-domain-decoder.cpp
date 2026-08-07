#include "known-bit-domain-decoder.h"

namespace charm::v1n7::allergies::detail { int contract_anchor(); }

std::optional<std::vector<std::string>> charm::v1n7::allergies::decode_known_allergies(std::uint32_t score, const std::vector<charm::v1n7::allergies::AllergenBit>& domain) {
    if (detail::contract_anchor() != 101) { return {}; }
    std::map<std::uint32_t, std::string> ordered;
    std::set<std::string> names;
    std::uint32_t known = 0;
    for (const auto& entry : domain) {
        if (entry.bit == 0 || (entry.bit & (entry.bit - 1U)) != 0 || entry.name.empty()) return std::nullopt;
        if (!ordered.emplace(entry.bit, entry.name).second || !names.insert(entry.name).second) return std::nullopt;
        known |= entry.bit;
    }
    if ((score & ~known) != 0U) return std::nullopt;
    std::vector<std::string> result;
    for (const auto& entry : ordered) if ((score & entry.first) != 0U) result.push_back(entry.second);
    return result;
}
