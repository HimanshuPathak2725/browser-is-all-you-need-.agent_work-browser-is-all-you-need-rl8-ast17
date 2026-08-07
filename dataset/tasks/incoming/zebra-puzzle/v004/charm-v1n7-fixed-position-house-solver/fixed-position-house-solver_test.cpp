#include "fixed-position-house-solver.h"

#include <cassert>

using namespace charm::v1n7::zebra_puzzle;
int main(){auto r=solve_house_assignment(3,{"zebra","water","coffee"},{{"water",1}});assert(r&&r->item_at_position==(std::vector<std::string>{"coffee","water","zebra"}));assert(solve_house_assignment(0,{},{})->item_at_position.empty());assert(!solve_house_assignment(2,{"a"},{}));assert(!solve_house_assignment(2,{"a","a"},{}));assert(!solve_house_assignment(2,{"a","b"},{{"x",0}}));return 0;}
