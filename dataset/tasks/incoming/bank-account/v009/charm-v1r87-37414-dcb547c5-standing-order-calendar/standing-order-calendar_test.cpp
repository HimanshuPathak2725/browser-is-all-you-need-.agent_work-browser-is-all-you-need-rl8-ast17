#include "standing-order-calendar.hpp"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::bank_account;
int main() {
CHECK(settle_standing_orders({{5,2},{6,3}},0,{}).value()==std::map<int,std::int64_t>{{7,5}});
CHECK(settle_standing_orders({{0,4}},0,{0,1}).value()==std::map<int,std::int64_t>{{2,4}});
CHECK(settle_standing_orders({},6,{}).value().empty());
CHECK(!settle_standing_orders({{-1,2}},0,{}));
CHECK(!settle_standing_orders({},7,{}));
return 0;
}
