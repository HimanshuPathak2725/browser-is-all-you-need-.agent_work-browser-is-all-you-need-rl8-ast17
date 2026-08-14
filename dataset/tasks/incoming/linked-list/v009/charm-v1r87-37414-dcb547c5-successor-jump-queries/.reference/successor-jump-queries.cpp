#include "successor-jump-queries.h"

namespace charm::v1r87_37414::linked_list {
std::optional<std::vector<int>> successor_jump_queries(const std::vector<int>& next, const std::vector<JumpQuery>& queries) {
for(int n:next)if(n<-1||n>=static_cast<int>(next.size()))return std::nullopt;
std::vector<std::vector<int>> up(64,next);
for(int b=1;b<64;++b)for(std::size_t i=0;i<next.size();++i)up[b][i]=up[b-1][i]<0?-1:up[b-1][up[b-1][i]];
std::vector<int> out;
for(auto q:queries){if(q.start<0||q.start>=static_cast<int>(next.size()))return std::nullopt;
int at=q.start;
for(int b=0;b<64&&at>=0;++b)if(q.steps&(std::uint64_t{1}<<b))at=up[b][at];
out.push_back(at);
}return out;

}
}
