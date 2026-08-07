#include "cyclic-interval-overlap.hpp"

#include <cassert>

using namespace charm::v1n7::clock;
int main() {
    assert(cyclic_overlap_minutes({1380,120},{0,90})==60);
    assert(cyclic_overlap_minutes({0,0},{0,1440})==0);
    assert(cyclic_overlap_minutes({0,1440},{500,1440})==1440);
    assert(!cyclic_overlap_minutes({-1,1},{0,1}));
    assert(!cyclic_overlap_minutes({0,1441},{0,1}));
    return 0;
}
