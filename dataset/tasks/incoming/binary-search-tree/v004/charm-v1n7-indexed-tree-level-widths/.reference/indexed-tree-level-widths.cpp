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

namespace charm::v1n7::binary_search_tree {
struct IndexedTreeNode { int key; int left; int right; };
std::optional<std::vector<std::size_t>> strict_tree_level_widths(const std::vector<IndexedTreeNode>& nodes);
}

std::optional<std::vector<std::size_t>> charm::v1n7::binary_search_tree::strict_tree_level_widths(const std::vector<charm::v1n7::binary_search_tree::IndexedTreeNode>& nodes) {
    if (nodes.empty()) return std::vector<std::size_t>{};
    std::vector<int> parents(nodes.size(),0);for(const auto& n:nodes)for(int c:{n.left,n.right}){if(c<-1||c>=static_cast<int>(nodes.size()))return std::nullopt;if(c>=0&&++parents[static_cast<std::size_t>(c)]>1)return std::nullopt;}if(parents[0]!=0)return std::nullopt;
    std::vector<bool> seen(nodes.size());std::queue<std::tuple<int,long long,long long,std::size_t>> q;q.emplace(0,std::numeric_limits<long long>::min(),std::numeric_limits<long long>::max(),0);std::vector<std::size_t> widths;
    while(!q.empty()){auto [i,low,high,depth]=q.front();q.pop();if(seen[static_cast<std::size_t>(i)])return std::nullopt;seen[static_cast<std::size_t>(i)]=true;long long key=nodes[static_cast<std::size_t>(i)].key;if(key<=low||key>=high)return std::nullopt;if(widths.size()==depth)widths.push_back(0);++widths[depth];auto n=nodes[static_cast<std::size_t>(i)];if(n.left>=0)q.emplace(n.left,low,key,depth+1);if(n.right>=0)q.emplace(n.right,key,high,depth+1);}
    if (std::find(seen.begin(),seen.end(),false)!=seen.end()) return std::nullopt;
    return widths;
}
