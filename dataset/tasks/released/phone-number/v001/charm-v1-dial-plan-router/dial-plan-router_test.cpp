#include "dial-plan-router.cpp"
#include <cassert>
#include <string>
#include <utility>
using charm::phone::DialPlan;
int main() {
    DialPlan plan;
    assert(!plan.add("", "root") && !plan.add("12a", "bad") && !plan.add("12", ""));
    assert(plan.add("1", "country") && plan.add("1212", "city") && plan.add("1212555", "exchange"));
    assert(!plan.add("1", "duplicate"));
    assert(plan.route("12125550123") == std::make_optional(std::make_pair(std::string("exchange"), std::string("0123"))));
    assert(plan.route("199") == std::make_optional(std::make_pair(std::string("country"), std::string("99"))));
    assert(!plan.route("999") && !plan.route("12x"));
    assert(plan.route("1212") == std::make_optional(std::make_pair(std::string("city"), std::string(""))));
    return 0;
}
