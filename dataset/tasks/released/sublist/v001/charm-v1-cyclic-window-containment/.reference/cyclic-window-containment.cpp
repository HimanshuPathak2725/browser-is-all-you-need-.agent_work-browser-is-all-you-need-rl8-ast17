#include <cstddef>
#include <optional>
#include <vector>
namespace charm::sublist {
inline std::optional<std::size_t> cyclic_find(const std::vector<int>& host, const std::vector<int>& pattern) {
    if (pattern.empty()) return 0;
    if (host.empty() || pattern.size() > host.size()) return std::nullopt;
    for (std::size_t start = 0; start < host.size(); ++start) {
        bool matches = true;
        for (std::size_t i = 0; i < pattern.size(); ++i)
            if (host[(start + i) % host.size()] != pattern[i]) { matches = false; break; }
        if (matches) return start;
    }
    return std::nullopt;
}
}
