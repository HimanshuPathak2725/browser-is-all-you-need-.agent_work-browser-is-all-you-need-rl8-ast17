#include "cursor-gap-list.cpp"
#include <cassert>
#include <vector>
using charm::list::GapList;
int main() {
    GapList list;
    assert(list.cursor() == 0 && !list.erase_next());
    list.insert(1); list.insert(2); list.insert(3);
    assert((list.values() == std::vector<int>{1,2,3}) && list.cursor() == 3);
    assert(list.move(-2) && list.cursor() == 1);
    list.insert(9);
    assert((list.values() == std::vector<int>{1,9,2,3}) && list.cursor() == 2);
    assert(list.erase_next() == 2 && list.cursor() == 2);
    assert(!list.move(-3) && list.cursor() == 2);
    assert(!list.move(9) && (list.values() == std::vector<int>{1,9,3}));
    return 0;
}
