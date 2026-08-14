#include "billing-pulse-summary.cpp"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::phone_number;
int main() {
CHECK(summarize_billing_pulses({{"a",0,61},{"a",70,130}},60).value().at("a")==3);
CHECK(summarize_billing_pulses({},30).value().empty());
CHECK(summarize_billing_pulses({{"x",2,3}},10).value().at("x")==1);
CHECK(!summarize_billing_pulses({{"",0,1}},1));
CHECK(!summarize_billing_pulses({},0));
return 0;
}
