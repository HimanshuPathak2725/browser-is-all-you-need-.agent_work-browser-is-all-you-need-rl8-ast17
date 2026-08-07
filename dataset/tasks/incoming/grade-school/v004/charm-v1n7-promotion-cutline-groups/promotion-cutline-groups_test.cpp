#include "promotion-cutline-groups.cpp"

#include <cassert>

using namespace charm::v1n7::grade_school;
int main(){auto r=promotion_cutline_ids({{"a",1,90},{"b",1,80},{"c",1,80},{"d",2,70}},{{1,2},{2,0}});assert(r&&*r==(std::vector<std::string>{"a","b","c"}));assert(promotion_cutline_ids({},{})->empty());assert(!promotion_cutline_ids({{"a",0,1}},{}));assert(!promotion_cutline_ids({{"a",1,1},{"a",1,2}},{}));assert(!promotion_cutline_ids({},{{13,1}}));return 0;}
