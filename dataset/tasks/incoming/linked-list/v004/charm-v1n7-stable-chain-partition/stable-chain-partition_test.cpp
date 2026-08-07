#include "stable-chain-partition.cpp"

#include <cassert>

using charm::v1n7::linked_list::stable_partition_owned_chain;
int main(){auto r=stable_partition_owned_chain({3,1,2,1,4},3);assert(r.values==(std::vector<int>{1,2,1,3,4})&&r.relinked==5);assert(stable_partition_owned_chain({},0).relinked==0);assert(stable_partition_owned_chain({1},2).values==std::vector<int>{1});assert(stable_partition_owned_chain({2,3},0).values==(std::vector<int>{2,3}));assert(stable_partition_owned_chain({-1,2},1).values==(std::vector<int>{-1,2}));return 0;}
