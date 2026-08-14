#include "weekly-recurrence-wait.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::clock;
int main() {
CHECK(wait_to_next_weekly_slot(100,{120,90})==20);
CHECK(wait_to_next_weekly_slot(100,{100})==10080);
CHECK(wait_to_next_weekly_slot(10079,{0})==1);
CHECK(!wait_to_next_weekly_slot(0,{}));
CHECK(!wait_to_next_weekly_slot(0,{1,1}));
return 0;
}
