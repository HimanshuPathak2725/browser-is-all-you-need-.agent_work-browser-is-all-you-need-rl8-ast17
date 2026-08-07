#include "complete-house-solution-validator.h"

#include <cassert>

using namespace charm::v1n7::zebra_puzzle;
int main(){assert(validate_complete_house_solution({{"red","tea"},{"blue","water"}},2,{{"red","tea"}},{{"tea","water"}}));assert(validate_complete_house_solution({},0,{},{}));assert(!validate_complete_house_solution({{"a","a"}},2,{},{}));assert(!validate_complete_house_solution({{"a"},{"a"}},1,{},{}));assert(!validate_complete_house_solution({{"a"}},1,{{"a","x"}},{}));return 0;}
