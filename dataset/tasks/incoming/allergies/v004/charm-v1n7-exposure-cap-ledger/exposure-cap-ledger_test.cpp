#include "exposure-cap-ledger.cpp"

#include <cassert>

using namespace charm::v1n7::allergies;
int main() {
    auto r=exceeded_exposure_caps({{"dust",3},{"pollen",4}},{{"pollen",3},{"dust",5},{"pollen",3}});
    assert(r && *r==(std::vector<std::pair<std::string,int>>{{"dust",2},{"pollen",2}}));
    assert(exceeded_exposure_caps({{"x",0}},{})->empty());
    assert(!exceeded_exposure_caps({{"x",1},{"x",2}},{}));
    assert(!exceeded_exposure_caps({{"x",1}},{{"y",1}}));
    assert(!exceeded_exposure_caps({{"x",1}},{{"x",-1}}));
    return 0;
}
