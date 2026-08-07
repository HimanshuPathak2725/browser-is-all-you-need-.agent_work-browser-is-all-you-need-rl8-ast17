#pragma once
#include <algorithm>
#include <array>
#include <map>
#include <optional>
namespace charm::yacht {
enum class JokerCategory { yacht, full_house, four_kind, choice };
inline int fixed_joker_score(const std::array<int,5>& dice, JokerCategory category) {
    std::map<int,int> counts; int sum=0; for(int die:dice){++counts[die];sum+=die;}
    if(category==JokerCategory::choice) return sum;
    if(category==JokerCategory::yacht) return counts.size()==1 ? 50 : 0;
    if(category==JokerCategory::full_house) { bool two=false,three=false; for(const auto& item:counts){two=two||item.second==2;three=three||item.second==3;} return two&&three?25:0; }
    for(const auto& item:counts) if(item.second>=4) return sum;
    return 0;
}
inline std::optional<int> joker_score(const std::array<int,5>& dice, JokerCategory category) {
    int jokers=0; for(int die:dice){if(die==0)++jokers;else if(die<1||die>6)return std::nullopt;}
    if(jokers>0)return std::nullopt;
    if(jokers==0)return fixed_joker_score(dice,category);
    int best=0;
    for(int face=1;face<=6;++face){auto replaced=dice; for(int& die:replaced)if(die==0)die=face; best=std::max(best,fixed_joker_score(replaced,category));}
    return best;
}
}
