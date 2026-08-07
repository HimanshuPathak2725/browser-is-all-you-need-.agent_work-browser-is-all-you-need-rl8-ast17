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

namespace charm::v1n7::kindergarten_garden {

std::optional<std::vector<std::pair<std::string,std::vector<std::string>>>> assign_rotating_cups(const std::vector<std::string>& children, const std::vector<std::string>& labels, long long start_child);
}

std::optional<std::vector<std::pair<std::string,std::vector<std::string>>>> charm::v1n7::kindergarten_garden::assign_rotating_cups(const std::vector<std::string>& children,const std::vector<std::string>& labels,long long start_child){std::set<std::string> names;for(const auto& child:children)if(child.empty()||!names.insert(child).second)return std::nullopt;for(const auto& label:labels)if(label.empty())return std::nullopt;if(children.empty()){if(!labels.empty())return std::nullopt;return std::vector<std::pair<std::string,std::vector<std::string>>>{};}long long n=static_cast<long long>(children.size());long long start=start_child%n;if(start<0)start+=n;std::vector<std::pair<std::string,std::vector<std::string>>> out;for(const auto& child:children)out.push_back({child,{}});for(std::size_t i=0;i<labels.size();++i)out[static_cast<std::size_t>((start+static_cast<long long>(i))%n)].second.push_back(labels[i]);return out;}
