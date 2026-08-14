#include "postfix-dice-rule.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::yacht;
int main() {
CHECK(evaluate_postfix_dice_rule({1,1,3},{"sum","count:1","*"})==10);
CHECK(evaluate_postfix_dice_rule({6},{"max","2","+"})==8);
CHECK(!evaluate_postfix_dice_rule({},{"max"}));
CHECK(!evaluate_postfix_dice_rule({0},{"sum"}));
CHECK(!evaluate_postfix_dice_rule({1},{"1","1"}));
return 0;
}
