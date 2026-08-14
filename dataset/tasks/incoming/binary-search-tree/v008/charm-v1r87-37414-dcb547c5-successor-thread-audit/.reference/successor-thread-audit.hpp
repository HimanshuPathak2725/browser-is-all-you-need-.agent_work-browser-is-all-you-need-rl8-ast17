#pragma once

#include <algorithm>
#include <array>
#include <cctype>
#include <climits>
#include <cstdlib>
#include <future>
#include <cmath>
#include <complex>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <functional>
#include <iterator>
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

namespace charm::v1r87_37414::binary_search_tree {
struct ThreadedNode { int key; int left; int right; int successor; };
std::optional<std::vector<int>> audit_successor_threads(const std::vector<ThreadedNode>& nodes, int root);
}

namespace charm::v1r87_37414::binary_search_tree {
inline std::optional<std::vector<int>> audit_successor_threads(const std::vector<ThreadedNode>& nodes, int root) {
if(nodes.empty())return root==-1?std::optional<std::vector<int>>{std::vector<int>{}}:std::nullopt;
if(root<0||root>=static_cast<int>(nodes.size()))return std::nullopt;
std::vector<int> seen(nodes.size()),order;
std::function<bool(int,std::optional<int>,std::optional<int>)> dfs=[&](int i,std::optional<int>lo,std::optional<int>hi){if(i==-1)return true;
if(i<0||i>=static_cast<int>(nodes.size())||seen[i])return false;
const auto&n=nodes[i];
if((lo&&n.key<=*lo)||(hi&&n.key>=*hi))return false;
seen[i]=1;
return dfs(n.left,lo,n.key)&&(order.push_back(i),true)&&dfs(n.right,n.key,hi);
};
if(!dfs(root,std::nullopt,std::nullopt)||std::any_of(seen.begin(),seen.end(),[](int x){return !x;}))return std::nullopt;
std::vector<int> bad;
for(std::size_t k=0;k<order.size();++k){int expected=k+1<order.size()?order[k+1]:-1;
if(nodes[order[k]].successor!=expected)bad.push_back(order[k]);
}std::sort(bad.begin(),bad.end());
return bad;

}
}
