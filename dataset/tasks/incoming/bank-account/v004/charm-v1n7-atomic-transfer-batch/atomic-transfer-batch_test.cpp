#include "atomic-transfer-batch.cpp"

#include <cassert>

using namespace charm::v1n7::bank_account;
int main() {
    auto r=settle_transfer_batch({{"b",5},{"a",10}},{{"a","b",4},{"b","a",2}});
    assert(r && *r==(std::vector<std::pair<std::string,long long>>{{"a",8},{"b",7}}));
    assert(settle_transfer_batch({},{})->empty());
    assert(!settle_transfer_batch({{"a",1},{"a",2}},{}));
    assert(!settle_transfer_batch({{"a",1},{"b",0}},{{"a","b",2}}));
    assert(!settle_transfer_batch({{"a",1}},{{"a","a",1}}));
    return 0;
}
