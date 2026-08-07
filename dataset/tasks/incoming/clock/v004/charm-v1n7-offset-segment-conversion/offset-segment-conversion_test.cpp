#include "offset-segment-conversion.cpp"

#include <cassert>

using namespace charm::v1n7::clock;
int main() {
    assert((local_readings_to_utc({0,90,150},{{0,60},{120,120}}).value()==std::vector<int>{1380,30,30}));
    assert(!local_readings_to_utc({},{}));
    assert(!local_readings_to_utc({},{{1,0}}));
    assert(!local_readings_to_utc({-1},{{0,0}}));
    assert(!local_readings_to_utc({},{{0,0},{0,1}}));
    return 0;
}
