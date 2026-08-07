#include <algorithm>
#include <vector>
namespace charm::clockwork {
struct Window { int begin; int end; };
inline std::vector<Window> intersect_weekly(Window a, Window b) {
    constexpr int week = 7 * 24 * 60;
    const auto expand = [=](Window input) {
        std::vector<Window> out;
        if (input.begin < 0 || input.begin >= week || input.end < 0 || input.end >= week || input.begin == input.end) return out;
        if (input.begin < input.end) out.push_back(input);
        else { out.push_back({input.begin, week}); out.push_back({0, input.end}); }
        return out;
    };
    std::vector<Window> result;
    for (Window left : expand(a)) for (Window right : expand(b)) {
        const int begin = std::max(left.begin, right.begin);
        const int end = std::min(left.end, right.end);
        if (begin <= end) result.push_back({begin, end});
    }
    std::sort(result.begin(), result.end(), [](Window x, Window y) { return x.begin < y.begin; });
    std::vector<Window> merged;
    for (Window item : result) {
        if (!merged.empty() && item.begin <= merged.back().end) merged.back().end = std::max(merged.back().end, item.end);
        else merged.push_back(item);
    }
    return merged;
}
}
