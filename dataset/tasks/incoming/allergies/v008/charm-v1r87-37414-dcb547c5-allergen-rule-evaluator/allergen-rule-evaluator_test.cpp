#include "allergen-rule-evaluator.h"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::allergies;
int main() {
require_case(evaluate_allergen_rule("(milk&!egg)",{"milk"})==true);
require_case(evaluate_allergen_rule(" (milk | egg) ",{"egg"})==true);
require_case(evaluate_allergen_rule("!milk",{})==true);
require_case(!evaluate_allergen_rule("milk&egg",{"milk"}));
require_case(!evaluate_allergen_rule("Milk",{}));
return 0;
}
