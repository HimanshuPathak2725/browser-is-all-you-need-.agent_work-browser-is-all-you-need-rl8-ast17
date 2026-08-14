#include "minimum-unique-clue-subset.h"

namespace charm::v1r87_37414::zebra_puzzle {
std::optional<std::vector<std::size_t>> minimum_unique_clue_subset(std::uint64_t candidate_mask, std::size_t target, const std::vector<std::uint64_t>& eliminated_by_clue) {
if(candidate_mask==0||target>=63||!(candidate_mask&(std::uint64_t{1}<<target))||eliminated_by_clue.size()>20)return std::nullopt;
for(auto m:eliminated_by_clue)if((m&~candidate_mask)||(m&(std::uint64_t{1}<<target)))return std::nullopt;
std::vector<std::size_t> best;
bool found=false;
std::uint64_t limit=std::uint64_t{1}<<eliminated_by_clue.size();
for(std::uint64_t bits=0;bits<limit;++bits){std::uint64_t remain=candidate_mask;
std::vector<std::size_t> pick;
for(std::size_t i=0;i<eliminated_by_clue.size();++i)if(bits&(std::uint64_t{1}<<i)){remain&=~eliminated_by_clue[i];
pick.push_back(i);
}
if(remain==(std::uint64_t{1}<<target)&&(!found||pick.size()<best.size()||(pick.size()==best.size()&&pick<best))){best=pick;
found=true;
}}
if(!found)return std::vector<std::size_t>{};
return best;

}
}
