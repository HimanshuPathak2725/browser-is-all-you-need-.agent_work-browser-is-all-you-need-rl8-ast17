#include "owned-chain-erasures.h"

#include <cassert>

using charm::v1n7::linked_list::erase_owned_chain_positions;
int main(){auto r=erase_owned_chain_positions({10,20,30,40},{1,1});assert(r&&r->removed==(std::vector<int>{20,30})&&r->remaining==(std::vector<int>{10,40}));assert(erase_owned_chain_positions({},{})->remaining.empty());assert(!erase_owned_chain_positions({}, {0}));assert(erase_owned_chain_positions({1},{0})->remaining.empty());assert(!erase_owned_chain_positions({1,2},{2}));return 0;}
