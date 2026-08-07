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

namespace charm::v1n7::linked_list {
struct ChainPartition { std::vector<int> values; std::size_t relinked; };
ChainPartition stable_partition_owned_chain(const std::vector<int>& values, int pivot);
}

charm::v1n7::linked_list::ChainPartition charm::v1n7::linked_list::stable_partition_owned_chain(const std::vector<int>& values,int pivot){struct Node{int value;std::unique_ptr<Node> next;explicit Node(int v):value(v){}};std::unique_ptr<Node> input;for(auto it=values.rbegin();it!=values.rend();++it){auto n=std::make_unique<Node>(*it);n->next=std::move(input);input=std::move(n);}std::unique_ptr<Node> low,high;Node* low_tail=nullptr;Node* high_tail=nullptr;std::size_t moved=0;while(input){auto node=std::move(input);input=std::move(node->next);Node* raw=node.get();if(node->value<pivot){if(low_tail)low_tail->next=std::move(node);else low=std::move(node);low_tail=raw;}else{if(high_tail)high_tail->next=std::move(node);else high=std::move(node);high_tail=raw;}++moved;}if(low_tail)low_tail->next=std::move(high);else low=std::move(high);ChainPartition result{{},moved};for(Node* n=low.get();n;n=n->next.get())result.values.push_back(n->value);return result;}
