#include "parallel-rare-offsets.h"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::parallel_letter_frequency;
int main() {
require_case(parallel_rare_letter_offsets({"ab","aca"},2).value()==std::vector<std::size_t>{1,3});
require_case(parallel_rare_letter_offsets({},3).value().empty());
require_case(parallel_rare_letter_offsets({""},1).value().empty());
require_case(!parallel_rare_letter_offsets({"A"},1));
require_case(!parallel_rare_letter_offsets({},0));
return 0;
}
