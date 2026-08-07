#include "ordered-adjacency-permutation-solver.cpp"

#include <cassert>

using namespace charm::v1n7::zebra_puzzle;
int main(){auto r=solve_ordered_adjacency({"c","a","b"},{{"a","c"}},{{"b","c"}});assert(r&&*r&&**r==(std::vector<std::string>{"a","b","c"}));auto none=solve_ordered_adjacency({"a","b"},{{"a","b"},{"b","a"}},{});assert(none&&!*none);assert(!solve_ordered_adjacency({"a","a"},{},{}));assert(!solve_ordered_adjacency({"a"},{{"a","x"}},{}));assert(solve_ordered_adjacency({}, {}, {})->value().empty());return 0;}
