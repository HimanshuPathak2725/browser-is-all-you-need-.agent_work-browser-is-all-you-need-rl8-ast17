#include "paired-cohort-deltas.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::grade_school;
int main() {
auto s=summarize_paired_cohort_deltas({{"a",2},{"b",5},{"c",4}},{{"a",3},{"b",3},{"c",4}}).value();CHECK(s.improved==1&&s.equal==1&&s.declined==1&&s.lower_median==0);
CHECK(summarize_paired_cohort_deltas({{"a",1},{"b",1}},{{"a",3},{"b",0}}).value().lower_median==-1);
CHECK(!summarize_paired_cohort_deltas({},{}));
CHECK(!summarize_paired_cohort_deltas({{"a",1}},{{"b",1}}));
CHECK(!summarize_paired_cohort_deltas({{"",1}},{{"",2}}));
return 0;
}
