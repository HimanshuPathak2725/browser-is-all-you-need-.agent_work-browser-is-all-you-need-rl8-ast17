#include "mergeable-frequency.cpp"
#include <array>
#include <cassert>
#include <limits>
using charm::frequency::MergeCounter;
int main() {
    MergeCounter counter;
    std::array<std::size_t,26> one{}; one[0]=2; one[25]=1;
    assert(!counter.merge("", one));
    assert(counter.merge("s1", one) && counter.merged_shards() == 1);
    assert(counter.count('a') == 2 && counter.count('A') == 2 && counter.count('z') == 1);
    assert(!counter.merge("s1", one) && counter.count('a') == 2);
    std::array<std::size_t,26> two{}; two[0]=3;
    assert(counter.merge("s2", two) && counter.count('a') == 5);
    assert(counter.count('?') == 0);
    std::array<std::size_t,26> huge{}; huge[0]=std::numeric_limits<std::size_t>::max();
    assert(!counter.merge("overflow", huge) && counter.merged_shards() == 2);
    return 0;
}
