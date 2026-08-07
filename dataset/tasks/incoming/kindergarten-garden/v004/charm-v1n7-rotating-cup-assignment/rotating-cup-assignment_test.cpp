#include "rotating-cup-assignment.cpp"

#include <cassert>

using charm::v1n7::kindergarten_garden::assign_rotating_cups;
int main(){auto r=assign_rotating_cups({"A","B","C"},{"x","y","z","w"},-1);assert((r&&r->at(2).second==std::vector<std::string>{"x","w"}&&r->at(0).second==std::vector<std::string>{"y"}));assert(assign_rotating_cups({}, {}, 9)->empty());assert(!assign_rotating_cups({}, {"x"}, 0));assert(!assign_rotating_cups({"A","A"},{},0));assert(!assign_rotating_cups({"A"},{""},0));return 0;}
