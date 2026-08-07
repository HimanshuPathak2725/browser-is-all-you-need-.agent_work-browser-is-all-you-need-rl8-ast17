#include "offset-civil-clock.h"
#include <cassert>
#include <string>
using charm::clockwork::OffsetClock;
int main() {
    const auto base = OffsetClock::at(23, 50, 120);
    assert(base.display() == "23:50 UTC+02:00");
    assert(base.plus_minutes(20).display() == "00:10 UTC+02:00");
    assert(OffsetClock::at(-1, -30, -90).display() == "22:30 UTC-01:30");
    assert(OffsetClock::at(12, 0, 120).same_instant(OffsetClock::at(10, 0, 0)));
    assert(!OffsetClock::at(12, 1, 120).same_instant(OffsetClock::at(10, 0, 0)));
    assert(OffsetClock::at(0, 0, 1440).same_instant(OffsetClock::at(0, 0, 0)));
    assert(base.plus_minutes(-1440).display() == base.display());
    return 0;
}
