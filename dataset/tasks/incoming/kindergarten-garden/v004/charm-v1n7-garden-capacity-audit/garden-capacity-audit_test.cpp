#include "garden-capacity-audit.h"

#include <cassert>

using namespace charm::v1n7::kindergarten_garden;
int main(){auto r=audit_garden_capacity({{"A",{{"C",2},{"R",1}}},{"B",{{"C",2}}}},{{"C",3},{"R",2}});assert(r&&*r==(std::vector<std::pair<std::string,int>>{{"C",1}}));assert(audit_garden_capacity({},{})->empty());assert(!audit_garden_capacity({{"A",{{"X",1}}}},{}));assert(!audit_garden_capacity({{"A",{{"X",1},{"X",1}}}},{{"X",3}}));assert(!audit_garden_capacity({{"A",{}},{"A",{}}},{}));return 0;}
