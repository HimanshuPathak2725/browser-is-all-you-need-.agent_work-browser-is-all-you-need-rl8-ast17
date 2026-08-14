#include "minimum-substring-block-cover.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::sublist;
int main() {
CHECK(minimum_substring_block_cover("abc","abcabc").value().blocks==2);
CHECK(minimum_substring_block_cover("abcd","ac").value().blocks==2);
CHECK(!minimum_substring_block_cover("a",""));
CHECK(!minimum_substring_block_cover("","a").value().possible);
CHECK(minimum_substring_block_cover("xyz","xy").value().blocks==1);
return 0;
}
