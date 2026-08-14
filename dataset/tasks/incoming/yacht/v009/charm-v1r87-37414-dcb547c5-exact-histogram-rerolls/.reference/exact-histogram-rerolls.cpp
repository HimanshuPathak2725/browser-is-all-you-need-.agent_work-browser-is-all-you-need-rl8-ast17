#include "exact-histogram-rerolls.h"

namespace charm::v1r87_37414::yacht {
std::optional<std::size_t> minimum_exact_histogram_rerolls(const std::vector<int>& dice, int sides, const std::vector<std::size_t>& target_counts) {
if(sides<=0||target_counts.size()!=static_cast<std::size_t>(sides)||std::accumulate(target_counts.begin(),target_counts.end(),std::size_t{0})!=dice.size())return std::nullopt;
std::vector<std::size_t> have(sides);
for(int d:dice){if(d<1||d>sides)return std::nullopt;
++have[d-1];
}std::size_t keep=0;
for(int f=0;f<sides;++f)keep+=std::min(have[f],target_counts[f]);
return dice.size()-keep;

}
}
