#include "indexed-chain-cycle-entry.h"

#include <cassert>

using charm::v1n7::linked_list::indexed_chain_cycle_entry;
int main(){auto r=indexed_chain_cycle_entry({1,2,1},0);assert(r&&*r&&**r==1);auto a=indexed_chain_cycle_entry({1,-1},0);assert(a&&!*a);auto e=indexed_chain_cycle_entry({},-1);assert(e&&!*e);assert(!indexed_chain_cycle_entry({2},0));assert(!indexed_chain_cycle_entry({},0));return 0;}
