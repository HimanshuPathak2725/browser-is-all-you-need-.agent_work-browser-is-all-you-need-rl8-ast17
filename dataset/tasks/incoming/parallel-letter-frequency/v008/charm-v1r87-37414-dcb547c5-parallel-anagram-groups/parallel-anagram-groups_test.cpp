#include "parallel-anagram-groups.h"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::parallel_letter_frequency;
int main() {
require_case(parallel_anagram_groups({"tea","ate","bat"},2).value()==(std::vector<std::vector<std::string>>{{"ate","tea"},{"bat"}}));
require_case(parallel_anagram_groups({},3).value().empty());
require_case(parallel_anagram_groups({"a"},9).value()==(std::vector<std::vector<std::string>>{{"a"}}));
require_case(!parallel_anagram_groups({"A"},1));
require_case(!parallel_anagram_groups({"a"},0));
return 0;
}
