#include <algorithm>
#include <array>
#include <climits>
#include <cstdlib>
#include <future>
#include <cmath>
#include <complex>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <functional>
#include <limits>
#include <map>
#include <memory>
#include <numeric>
#include <optional>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace charm::v1n7::zebra_puzzle {
struct OrderClue { std::string before; std::string after; }; struct AdjacentClue { std::string first; std::string second; };
std::optional<std::optional<std::vector<std::string>>> solve_ordered_adjacency(const std::vector<std::string>& labels, const std::vector<OrderClue>& orders, const std::vector<AdjacentClue>& adjacent);
}

std::optional<std::optional<std::vector<std::string>>> charm::v1n7::zebra_puzzle::solve_ordered_adjacency(const std::vector<std::string>& labels,const std::vector<charm::v1n7::zebra_puzzle::OrderClue>& orders,const std::vector<charm::v1n7::zebra_puzzle::AdjacentClue>& adjacent){if(labels.size()>8)return std::nullopt;std::set<std::string> domain(labels.begin(),labels.end());if(domain.size()!=labels.size()||domain.count("")!=0)return std::nullopt;auto known=[&](const std::string& a,const std::string& b){return a!=b&&domain.count(a)&&domain.count(b);};for(const auto& c:orders)if(!known(c.before,c.after))return std::nullopt;for(const auto& c:adjacent)if(!known(c.first,c.second))return std::nullopt;std::vector<std::string> candidate(domain.begin(),domain.end());do{std::map<std::string,std::size_t> pos;for(std::size_t i=0;i<candidate.size();++i)pos[candidate[i]]=i;bool ok=true;for(const auto& c:orders)ok=ok&&pos[c.before]<pos[c.after];for(const auto& c:adjacent)ok=ok&&(pos[c.first]+1==pos[c.second]||pos[c.second]+1==pos[c.first]);if(ok)return std::optional<std::vector<std::string>>{candidate};}while(std::next_permutation(candidate.begin(),candidate.end()));return std::optional<std::vector<std::string>>{};}
