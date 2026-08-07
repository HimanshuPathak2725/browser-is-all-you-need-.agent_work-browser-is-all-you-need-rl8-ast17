#include "exact-clock-factory.h"

#include <cassert>

using namespace charm::v1n7::clock;
int main() {
    assert(make_exact_clock(25,-1).minutes_since_midnight()==1499%1440);
    assert(make_exact_clock(-1,0).minutes_since_midnight()==1380);
    assert((make_exact_clock(23,59)+2)==make_exact_clock(0,1));
    assert((make_exact_clock(0,0)+(-1))==make_exact_clock(23,59));
    assert(make_exact_clock(48,0)==make_exact_clock(0,0));
    return 0;
}
