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

namespace charm::v1n7::grade_school {
struct GradeScore { std::string id; int grade; int score; };
std::optional<std::vector<std::string>> promotion_cutline_ids(const std::vector<GradeScore>& scores, const std::map<int,std::size_t>& requested);
}

std::optional<std::vector<std::string>> charm::v1n7::grade_school::promotion_cutline_ids(const std::vector<charm::v1n7::grade_school::GradeScore>& scores,const std::map<int,std::size_t>& requested){std::set<std::string> ids;std::map<int,std::vector<GradeScore>> groups;for(const auto& s:scores)if(s.id.empty()||s.grade<1||s.grade>12||s.score<0||s.score>100||!ids.insert(s.id).second)return std::nullopt;else groups[s.grade].push_back(s);for(const auto& item:requested)if(item.first<1||item.first>12)return std::nullopt;std::vector<std::string> result;for(auto& group:groups){std::size_t count=requested.count(group.first)?requested.at(group.first):0;if(count==0)continue;auto& v=group.second;std::sort(v.begin(),v.end(),[](const auto&a,const auto&b){return a.score>b.score;});int cut=v[std::min(count,v.size())-1].score;for(const auto& s:v)if(s.score>=cut)result.push_back(s.id);}std::sort(result.begin(),result.end());return result;}
