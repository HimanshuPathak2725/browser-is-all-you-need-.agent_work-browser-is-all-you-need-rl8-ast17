#include "allergen-rule-evaluator.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::allergies;
int main() {
CHECK(evaluate_allergen_rule("(milk&!egg)",{"milk"})==true);
CHECK(evaluate_allergen_rule(" (milk | egg) ",{"egg"})==true);
CHECK(evaluate_allergen_rule("!milk",{})==true);
CHECK(!evaluate_allergen_rule("milk&egg",{"milk"}));
CHECK(!evaluate_allergen_rule("Milk",{}));
return 0;
}
