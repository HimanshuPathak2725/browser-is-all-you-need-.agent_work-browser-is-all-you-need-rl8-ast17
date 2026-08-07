#pragma once
#include <algorithm>
#include <cmath>
#include <functional>
#include <map>
#include <optional>
#include <set>
#include <string>
#include <vector>
namespace charm::zebra {
enum class ClueKind { same_house, adjacent, immediately_left };
struct Clue { ClueKind kind; std::string a; std::string b; };
inline bool clues_hold(const std::map<std::string,int>& assignment, const std::vector<Clue>& clues) {
    for (const Clue& clue : clues) {
        const auto a=assignment.find(clue.a), b=assignment.find(clue.b);
        if(a==assignment.end()||b==assignment.end())return false;
        if(clue.kind==ClueKind::same_house && a->second!=b->second)return false;
        if(clue.kind==ClueKind::adjacent && std::abs(a->second-b->second)!=1)return false;
        if(clue.kind==ClueKind::immediately_left && a->second+1!=b->second)return false;
    }
    return true;
}
inline std::optional<std::map<std::string,int>> solve_unique(int houses, const std::vector<std::vector<std::string>>& categories, const std::vector<Clue>& clues) {
    if(houses<=0||categories.empty())return std::nullopt;
    std::set<std::string> items;
    for(const auto& category:categories){if(category.size()!=static_cast<std::size_t>(houses))return std::nullopt;for(const auto& item:category)if(item.empty()||!items.insert(item).second)return std::nullopt;}
    for(const auto& clue:clues)if(items.count(clue.a)==0U||items.count(clue.b)==0U)return std::nullopt;
    std::map<std::string,int> current, solution; int count=0;
    std::function<void(std::size_t)> search=[&](std::size_t category_index){
        if(count>1)return;
        if(category_index==categories.size()){if(clues_hold(current,clues)){solution=current;++count;}return;}
        std::vector<int> order(static_cast<std::size_t>(houses)); for(int i=0;i<houses;++i)order[static_cast<std::size_t>(i)]=i;
        do { for(int i=0;i<houses;++i)current[categories[category_index][static_cast<std::size_t>(i)]]=order[static_cast<std::size_t>(i)]; search(category_index+1); } while(std::next_permutation(order.begin(),order.end()));
    };
    search(0); return count==1?std::optional<std::map<std::string,int>>(solution):std::nullopt;
}
}
