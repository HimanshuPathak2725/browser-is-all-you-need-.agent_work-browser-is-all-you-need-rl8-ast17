#include <algorithm>
#include <string>
#include <tuple>
#include <utility>
#include <vector>
namespace charm::bst {
class IntervalIndex {
public:
    bool add(int begin, int end, std::string label) {
        if (begin > end || label.empty()) return false;
        intervals_.push_back({begin, end, std::move(label)});
        return true;
    }
    std::vector<std::string> containing(int point) const {
        std::vector<const Interval*> matches;
        for (const Interval& interval : intervals_)
            if (interval.begin <= point && point <= interval.end) matches.push_back(&interval);
        std::sort(matches.begin(), matches.end(), [](const Interval* a, const Interval* b) {
            const long long alen = static_cast<long long>(a->end) - a->begin;
            const long long blen = static_cast<long long>(b->end) - b->begin;
            return std::tie(alen, a->label) < std::tie(blen, b->label);
        });
        std::vector<std::string> labels;
        for (const Interval* interval : matches) labels.push_back(interval->label);
        return labels;
    }
private:
    struct Interval { int begin; int end; std::string label; };
    std::vector<Interval> intervals_;
};
}
