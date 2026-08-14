#include "parallel-rare-offsets.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::parallel_letter_frequency;
int main() {
CHECK(parallel_rare_letter_offsets({"ab","aca"},2).value()==std::vector<std::size_t>{1,3});
CHECK(parallel_rare_letter_offsets({},3).value().empty());
CHECK(parallel_rare_letter_offsets({""},1).value().empty());
CHECK(!parallel_rare_letter_offsets({"A"},1));
CHECK(!parallel_rare_letter_offsets({},0));
return 0;
}
