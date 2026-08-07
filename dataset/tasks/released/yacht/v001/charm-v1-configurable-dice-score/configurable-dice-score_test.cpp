#include "configurable-dice-score.h"
#include <cassert>
using charm::yacht::Category;
using charm::yacht::RuleKind;
using charm::yacht::score;
int main() {
    assert(!score({1,2}, 6, {RuleKind::value_sum,1}));
    assert(!score({0,1,2,3,4}, 6, {RuleKind::straight,5}));
    assert(score({2,2,2,5,5}, 6, {RuleKind::exact_group,3}) == 6);
    assert(score({2,2,2,5,5}, 6, {RuleKind::exact_group,2}) == 10);
    assert(score({1,2,3,4,5}, 6, {RuleKind::straight,5}) == 15);
    assert(score({1,2,3,4,6}, 6, {RuleKind::straight,5}) == 0);
    assert(score({6,6,1,2,6}, 6, {RuleKind::value_sum,6}) == 18);
    assert(!score({1,2,3,4,5}, 6, {RuleKind::value_sum,7}));
    return 0;
}
