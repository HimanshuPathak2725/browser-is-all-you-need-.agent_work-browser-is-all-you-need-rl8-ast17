#include "unique-student-roster.h"

#include <cassert>

using namespace charm::v1n7::grade_school;
int main(){auto r=ordered_unique_roster({{"b",2,90},{"a",1,80},{"c",2,90}});assert(r&&r->at(0).id=="a"&&r->at(1).id=="b"&&r->at(2).id=="c");assert(ordered_unique_roster({})->empty());assert(!ordered_unique_roster({{"",1,1}}));assert(!ordered_unique_roster({{"a",1,1},{"a",2,2}}));assert(!ordered_unique_roster({{"a",13,1}}));return 0;}
