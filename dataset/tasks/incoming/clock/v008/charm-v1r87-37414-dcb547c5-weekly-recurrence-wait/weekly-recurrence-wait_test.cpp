#include "weekly-recurrence-wait.h"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::clock;
int main() {
require_case(wait_to_next_weekly_slot(100,{120,90})==20);
require_case(wait_to_next_weekly_slot(100,{100})==10080);
require_case(wait_to_next_weekly_slot(10079,{0})==1);
require_case(!wait_to_next_weekly_slot(0,{}));
require_case(!wait_to_next_weekly_slot(0,{1,1}));
return 0;
}
