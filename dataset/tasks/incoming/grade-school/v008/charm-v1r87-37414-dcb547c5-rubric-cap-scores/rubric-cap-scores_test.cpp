#include "rubric-cap-scores.h"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::grade_school;
int main() {
require_case(score_capped_rubrics({{"code",5},{"test",3}},{{"ann",{{"code",9},{"test",2}}}}).value().at("ann")==7);
require_case(score_capped_rubrics({{"x",1}},{{"a",{}}}).value().at("a")==0);
require_case(score_capped_rubrics({{"x",1}},{}).value().empty());
require_case(!score_capped_rubrics({{"x",0}},{}));
require_case(!score_capped_rubrics({{"x",1}},{{"a",{{"y",1}}}}));
return 0;
}
