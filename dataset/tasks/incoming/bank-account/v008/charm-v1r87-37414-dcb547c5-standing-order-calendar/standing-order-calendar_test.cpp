#include "standing-order-calendar.hpp"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::bank_account;
int main() {
require_case(settle_standing_orders({{5,2},{6,3}},0,{}).value()==std::map<int,std::int64_t>{{7,5}});
require_case(settle_standing_orders({{0,4}},0,{0,1}).value()==std::map<int,std::int64_t>{{2,4}});
require_case(settle_standing_orders({},6,{}).value().empty());
require_case(!settle_standing_orders({{-1,2}},0,{}));
require_case(!settle_standing_orders({},7,{}));
return 0;
}
