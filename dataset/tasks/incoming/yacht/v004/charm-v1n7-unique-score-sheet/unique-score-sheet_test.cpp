#include "unique-score-sheet.h"

#include <cassert>

using namespace charm::v1n7::yacht;
int main(){auto r=summarize_unique_score_sheet({{"sum",{1,1,1,1,1}},{"all-even",{1,2,2,2,2}}});assert(r&&*r==(std::array<int,3>{5,2,1}));assert(summarize_unique_score_sheet({})->at(0)==0);assert(!summarize_unique_score_sheet({{"sum",{1,1,1,1,1}},{"sum",{2,2,2,2,2}}}));assert(!summarize_unique_score_sheet({{"bad",{1,1,1,1,1}}}));assert(!summarize_unique_score_sheet({{"sum",{7,1,1,1,1}}}));return 0;}
