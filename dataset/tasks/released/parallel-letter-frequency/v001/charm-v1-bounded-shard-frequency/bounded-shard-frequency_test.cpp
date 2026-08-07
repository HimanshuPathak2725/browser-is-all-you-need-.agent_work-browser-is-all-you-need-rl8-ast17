#include "bounded-shard-frequency.h"
#include <cassert>
#include <vector>
using charm::frequency::count_bounded;
int main() {
    const auto empty = count_bounded({}, 4); assert(empty[0] == 0);
    const auto zero = count_bounded({"abc"}, 0); assert(zero[0] == 0);
    const auto one = count_bounded({"Aa! z", "bA", "123"}, 1);
    assert(one[0] == 3 && one[1] == 1 && one[25] == 1);
    const auto many = count_bounded({"Aa! z", "bA", "123"}, 99);
    assert(many == one);
    const auto mixed = count_bounded({"XYZ", "xyz", "x"}, 2);
    assert(mixed[23] == 3 && mixed[24] == 2 && mixed[25] == 2);
    const auto repeat = count_bounded({"parallel", "letter"}, 2);
    assert(repeat == count_bounded({"parallel", "letter"}, 2));
    return 0;
}
