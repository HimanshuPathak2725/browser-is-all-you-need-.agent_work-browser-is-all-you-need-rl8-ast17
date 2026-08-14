#include "wildcard-contiguous-matches.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::sublist;
int main() {
CHECK(wildcard_contiguous_matches("abac","a?").value()==std::vector<std::size_t>({0,2}));
CHECK(wildcard_contiguous_matches("aaa","aa").value()==std::vector<std::size_t>({0,1}));
CHECK(wildcard_contiguous_matches("","a").value().empty());
CHECK(wildcard_contiguous_matches("a","??").value().empty());
CHECK(!wildcard_contiguous_matches("a",""));
return 0;
}
