#include "harvest-crate-first-fit.h"

namespace charm::v1r87_37414::kindergarten_garden {
std::optional<std::vector<std::size_t>> first_fit_harvest_crates(const std::vector<std::int64_t>& weights, std::int64_t capacity) {
if(capacity<=0)return std::nullopt;
std::vector<std::int64_t> used;
std::vector<std::size_t> out;
for(auto w:weights){if(w<=0||w>capacity)return std::nullopt;
std::size_t i=0;
while(i<used.size()&&used[i]>capacity-w)++i;
if(i==used.size())used.push_back(0);
used[i]+=w;
out.push_back(i);
}return out;

}
}
