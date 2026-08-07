#include "string-rule-score.h"

#include <cassert>

using charm::v1n7::yacht::score_string_rule;
int main(){assert(score_string_rule("sum",{1,2,3,4,5})==15);assert(score_string_rule("all-even",{2,2,4,4,6})==18);assert(score_string_rule("three-match",{3,3,3,1,2})==12);assert(score_string_rule("full-run",{6,2,5,3,4})==30);assert(!score_string_rule("yacht",{1,1,1,1,1}));assert(!score_string_rule("sum",{0,1,2,3,4}));return 0;}
