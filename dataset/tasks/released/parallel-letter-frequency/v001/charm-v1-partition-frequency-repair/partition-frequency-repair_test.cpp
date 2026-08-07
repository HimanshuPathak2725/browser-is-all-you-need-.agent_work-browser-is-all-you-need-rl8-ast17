#include "partition-frequency-repair.h"
#include <cassert>
#include <map>
#include <vector>
using charm::frequency::count_partitioned;
int main() {
    assert(count_partitioned({}, 3).empty());
    assert(count_partitioned({"abc"}, 0).empty());
    const std::vector<std::string> docs{"Aa", "b!", "CcC", ""};
    const auto expected = std::map<char,std::size_t>{{'a',2},{'b',1},{'c',3}};
    assert(count_partitioned(docs, 1) == expected);
    assert(count_partitioned(docs, 2) == expected);
    assert(count_partitioned(docs, 99) == expected);
    assert(count_partitioned({"X", "y", "Z"}, 2).size() == 3);
    assert(count_partitioned(docs, 3) == count_partitioned(docs, 3));
    return 0;
}
