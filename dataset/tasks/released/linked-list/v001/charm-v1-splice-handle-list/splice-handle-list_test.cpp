#include "splice-handle-list.h"
#include <cassert>
#include <vector>
using charm::list::SpliceList;
int main() {
    SpliceList list;
    const auto a=list.push_back(1), b=list.push_back(2), c=list.push_back(3), d=list.push_back(4);
    assert((list.values() == std::vector<int>{1,2,3,4}));
    assert(list.splice_before(c,d,a));
    assert((list.values() == std::vector<int>{3,4,1,2}));
    assert(!list.splice_before(c,a,d));
    assert(list.erase(c));
    assert((list.values() == std::vector<int>{4,1,2}));
    assert(!list.erase(c) && !list.splice_before(c,b,a));
    assert(list.splice_before(b,b,d));
    assert((list.values() == std::vector<int>{2,4,1}));
    return 0;
}
