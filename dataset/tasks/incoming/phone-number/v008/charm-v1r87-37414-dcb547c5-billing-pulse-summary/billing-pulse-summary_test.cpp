#include "billing-pulse-summary.cpp"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::phone_number;
int main() {
require_case(summarize_billing_pulses({{"a",0,61},{"a",70,130}},60).value().at("a")==3);
require_case(summarize_billing_pulses({},30).value().empty());
require_case(summarize_billing_pulses({{"x",2,3}},10).value().at("x")==1);
require_case(!summarize_billing_pulses({{"",0,1}},1));
require_case(!summarize_billing_pulses({},0));
return 0;
}
