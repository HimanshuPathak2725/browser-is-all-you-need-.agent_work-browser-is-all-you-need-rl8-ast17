#include "parallel-anagram-groups.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::parallel_letter_frequency;
int main() {
CHECK(parallel_anagram_groups({"tea","ate","bat"},2).value()==(std::vector<std::vector<std::string>>{{"ate","tea"},{"bat"}}));
CHECK(parallel_anagram_groups({},3).value().empty());
CHECK(parallel_anagram_groups({"a"},9).value()==(std::vector<std::vector<std::string>>{{"a"}}));
CHECK(!parallel_anagram_groups({"A"},1));
CHECK(!parallel_anagram_groups({"a"},0));
return 0;
}
