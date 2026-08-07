#include "joker-rule-repair.h"
#include <array>
#include <cassert>
using charm::yacht::JokerCategory;
using charm::yacht::joker_score;
int main() {
    assert(!joker_score({0,0,1,2,3},JokerCategory::choice));
    assert(!joker_score({7,1,2,3,4},JokerCategory::choice));
    assert(joker_score({6,6,6,6,6},JokerCategory::yacht)==50);
    assert(joker_score({0,6,6,6,6},JokerCategory::yacht)==50);
    assert(joker_score({0,2,2,3,3},JokerCategory::full_house)==25);
    assert(joker_score({0,4,4,4,2},JokerCategory::four_kind)==18);
    assert(joker_score({0,1,2,3,4},JokerCategory::choice)==16);
    assert(joker_score({1,2,3,4,5},JokerCategory::four_kind)==0);
    return 0;
}
