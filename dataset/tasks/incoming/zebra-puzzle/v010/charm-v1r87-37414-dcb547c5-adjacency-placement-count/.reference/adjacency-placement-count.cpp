#include "adjacency-placement-count.h"

namespace charm::v1r87_37414::zebra_puzzle {
std::optional<std::size_t> count_adjacency_placements(std::vector<std::string> items, const std::vector<FixedPlacement>& fixed, const std::vector<std::pair<std::string,std::string>>& adjacent) {
if(items.size()>10||std::set<std::string>(items.begin(),items.end()).size()!=items.size()||std::any_of(items.begin(),items.end(),[](const auto&s){return s.empty();}))return std::nullopt;
std::map<std::string,std::size_t> forced;
std::set<std::size_t> used_pos;
for(const auto&f:fixed)if(f.position>=items.size()||!std::count(items.begin(),items.end(),f.item)||!forced.emplace(f.item,f.position).second||!used_pos.insert(f.position).second)return std::nullopt;
std::set<std::pair<std::string,std::string>> clues;
for(auto p:adjacent){if(p.first==p.second||!std::count(items.begin(),items.end(),p.first)||!std::count(items.begin(),items.end(),p.second))return std::nullopt;
if(p.second<p.first)std::swap(p.first,p.second);
if(!clues.insert(p).second)return std::nullopt;
}std::sort(items.begin(),items.end());
std::size_t count=0;
do{std::map<std::string,std::size_t> at;
for(std::size_t i=0;i<items.size();++i)at[items[i]]=i;
bool ok=true;
for(auto [s,p]:forced)ok&=at[s]==p;
for(auto [a,b]:clues)ok&=std::abs(static_cast<long long>(at[a])-static_cast<long long>(at[b]))==1;
count+=ok;
}while(std::next_permutation(items.begin(),items.end()));
return count;

}
}
