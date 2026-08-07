#include "value-fed-spiral-fill.cpp"

#include <cassert>

using charm::v1n7::spiral_matrix::fill_spiral_from_values;
int main(){assert((fill_spiral_from_values(2,3,{1,2,3,4,5,6}).value()==std::vector<std::vector<int>>{{1,2,3},{6,5,4}}));assert(fill_spiral_from_values(0,3,{})->empty());assert(!fill_spiral_from_values(1,2,{1}));assert(fill_spiral_from_values(1,3,{7,8,9})->at(0)==std::vector<int>({7,8,9}));assert(fill_spiral_from_values(3,1,{1,2,3})->at(2).at(0)==3);return 0;}
