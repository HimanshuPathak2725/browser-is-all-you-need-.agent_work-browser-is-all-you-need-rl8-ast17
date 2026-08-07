#include "partitioned-posting-sum.hpp"

#include <cassert>

using charm::v1n7::bank_account::partitioned_posting_sum;
int main() {
    assert(partitioned_posting_sum({5,-2,7,-1},3)==9);
    assert(partitioned_posting_sum({},2)==0);
    assert(!partitioned_posting_sum({},0));
    assert(partitioned_posting_sum({1,2},9)==3);
    assert(!partitioned_posting_sum({std::numeric_limits<long long>::max(),1},1));
    return 0;
}
