#include "rubric-cap-scores.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::grade_school;
int main() {
CHECK(score_capped_rubrics({{"code",5},{"test",3}},{{"ann",{{"code",9},{"test",2}}}}).value().at("ann")==7);
CHECK(score_capped_rubrics({{"x",1}},{{"a",{}}}).value().at("a")==0);
CHECK(score_capped_rubrics({{"x",1}},{}).value().empty());
CHECK(!score_capped_rubrics({{"x",0}},{}));
CHECK(!score_capped_rubrics({{"x",1}},{{"a",{{"y",1}}}}));
return 0;
}
