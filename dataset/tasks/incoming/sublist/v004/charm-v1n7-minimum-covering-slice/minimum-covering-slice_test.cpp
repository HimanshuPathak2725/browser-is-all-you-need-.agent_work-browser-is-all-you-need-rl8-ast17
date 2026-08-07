#include "minimum-covering-slice.h"

#include <cassert>

using charm::v1n7::sublist::minimum_covering_slice;
int main(){assert((minimum_covering_slice({1,2,1,3,2},{1,2,2})==std::pair<std::size_t,std::size_t>(1,5)));assert((minimum_covering_slice({1,2},{})==std::pair<std::size_t,std::size_t>(0,0)));assert(!minimum_covering_slice({1},{1,1}));assert((minimum_covering_slice({2,1,2,1},{1,2})==std::pair<std::size_t,std::size_t>(0,2)));assert(!minimum_covering_slice({}, {1}));return 0;}
