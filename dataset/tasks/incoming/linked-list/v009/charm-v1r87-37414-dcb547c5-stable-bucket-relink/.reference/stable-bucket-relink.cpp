#include "stable-bucket-relink.h"

namespace charm::v1r87_37414::linked_list {
std::optional<std::pair<int,std::vector<int>>> stable_bucket_relink(const std::vector<std::size_t>& buckets, std::size_t bucket_count) {
std::vector<std::vector<int>> groups(bucket_count);
for(std::size_t i=0;i<buckets.size();++i){if(buckets[i]>=bucket_count)return std::nullopt;
groups[buckets[i]].push_back(static_cast<int>(i));
}std::vector<int> order;
for(const auto&g:groups)order.insert(order.end(),g.begin(),g.end());
std::vector<int> next(buckets.size(),-1);
for(std::size_t i=1;i<order.size();++i)next[order[i-1]]=order[i];
return std::pair<int,std::vector<int>>{order.empty()?-1:order[0],next};

}
}
