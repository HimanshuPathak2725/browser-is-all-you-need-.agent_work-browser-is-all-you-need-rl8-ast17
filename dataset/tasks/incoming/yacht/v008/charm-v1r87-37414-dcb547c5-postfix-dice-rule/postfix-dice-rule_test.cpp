#include "postfix-dice-rule.h"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::yacht;
int main() {
require_case(evaluate_postfix_dice_rule({1,1,3},{"sum","count:1","*"})==10);
require_case(evaluate_postfix_dice_rule({6},{"max","2","+"})==8);
require_case(!evaluate_postfix_dice_rule({},{"max"}));
require_case(!evaluate_postfix_dice_rule({0},{"sum"}));
require_case(!evaluate_postfix_dice_rule({1},{"1","1"}));
return 0;
}
