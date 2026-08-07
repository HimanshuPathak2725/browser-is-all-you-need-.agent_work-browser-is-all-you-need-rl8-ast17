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

namespace charm::v1n7::yacht {

std::optional<std::pair<std::string,int>> best_declared_rule(const std::array<int,5>& dice, const std::vector<std::string>& rules);
}

std::optional<std::pair<std::string,int>> charm::v1n7::yacht::best_declared_rule(const std::array<int,5>& dice,const std::vector<std::string>& rules){if(rules.empty())return std::nullopt;auto score_rule=[&](const std::string& rule)->std::optional<int>{std::array<int,7> counts{};int sum=0;for(int die:dice){if(die<1||die>6)return std::nullopt;++counts[die];sum+=die;}if(rule=="sum")return sum;if(rule=="all-even")return std::all_of(dice.begin(),dice.end(),[](int d){return d%2==0;})?sum:0;if(rule=="three-match")return *std::max_element(counts.begin(),counts.end())>=3?sum:0;if(rule=="full-run"){std::set<int> faces(dice.begin(),dice.end());return faces==std::set<int>({1,2,3,4,5})||faces==std::set<int>({2,3,4,5,6})?30:0;}return std::nullopt;};std::set<std::string> seen;std::optional<std::pair<std::string,int>> best;for(const auto& rule:rules){if(!seen.insert(rule).second)return std::nullopt;auto score=score_rule(rule);if(!score)return std::nullopt;if(!best||*score<best->second||(*score==best->second&&rule<best->first))best=std::pair<std::string,int>{rule,*score};}return best;}
