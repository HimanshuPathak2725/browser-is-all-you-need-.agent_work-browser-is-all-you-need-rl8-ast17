#include "optional-wildcard-windows.cpp"

#include <cassert>

using charm::v1n7::sublist::optional_pattern_positions;
int main(){using O=std::optional<int>;assert((optional_pattern_positions({1,2,1,3},{O{1},O{}})==std::vector<std::size_t>{0,2}));assert(optional_pattern_positions({1},{}).size()==2);assert(optional_pattern_positions({}, {O{}}).empty());assert(optional_pattern_positions({1,1},{O{1}})==(std::vector<std::size_t>{0,1}));assert(optional_pattern_positions({1,2},{O{2}})==std::vector<std::size_t>{1});return 0;}
