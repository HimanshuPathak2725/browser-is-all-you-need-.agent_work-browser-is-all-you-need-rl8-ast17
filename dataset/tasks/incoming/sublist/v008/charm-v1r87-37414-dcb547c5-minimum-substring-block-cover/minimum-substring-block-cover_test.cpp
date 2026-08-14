#include "minimum-substring-block-cover.h"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::sublist;
int main() {
require_case(minimum_substring_block_cover("abc","abcabc").value().blocks==2);
require_case(minimum_substring_block_cover("abcd","ac").value().blocks==2);
require_case(!minimum_substring_block_cover("a",""));
require_case(!minimum_substring_block_cover("","a").value().possible);
require_case(minimum_substring_block_cover("xyz","xy").value().blocks==1);
return 0;
}
