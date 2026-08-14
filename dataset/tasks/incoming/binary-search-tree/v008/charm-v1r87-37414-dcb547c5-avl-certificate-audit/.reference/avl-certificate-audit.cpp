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
struct AvlNode { int key; int left; int right; };
std::optional<int> audit_avl_certificate(const std::vector<AvlNode>& nodes, int root);
}

namespace charm::v1r87_37414::binary_search_tree {
std::optional<int> audit_avl_certificate(const std::vector<AvlNode>& nodes, int root) {
if(nodes.empty())return root==-1?std::optional<int>{0}:std::nullopt;
if(root<0||root>=static_cast<int>(nodes.size()))return std::nullopt;
std::vector<int> state(nodes.size());
std::function<std::optional<int>(int,std::optional<int>,std::optional<int>)> dfs=[&](int i,std::optional<int>lo,std::optional<int>hi)->std::optional<int>{if(i==-1)return 0;
if(i<0||i>=static_cast<int>(nodes.size())||state[i])return std::nullopt;
const auto&n=nodes[i];
if((lo&&n.key<=*lo)||(hi&&n.key>=*hi))return std::nullopt;
state[i]=1;
auto a=dfs(n.left,lo,n.key),b=dfs(n.right,n.key,hi);
if(!a||!b||std::abs(*a-*b)>1)return std::nullopt;
state[i]=2;
return 1+std::max(*a,*b);
};
auto h=dfs(root,std::nullopt,std::nullopt);
if(!h||std::any_of(state.begin(),state.end(),[](int x){return x!=2;}))return std::nullopt;
return h;

}
}
