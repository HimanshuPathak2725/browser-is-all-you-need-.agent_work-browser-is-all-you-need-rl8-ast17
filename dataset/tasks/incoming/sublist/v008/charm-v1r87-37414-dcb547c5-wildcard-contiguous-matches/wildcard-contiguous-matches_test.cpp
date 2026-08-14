#include "wildcard-contiguous-matches.h"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::sublist;
int main() {
require_case(wildcard_contiguous_matches("abac","a?").value()==std::vector<std::size_t>({0,2}));
require_case(wildcard_contiguous_matches("aaa","aa").value()==std::vector<std::size_t>({0,1}));
require_case(wildcard_contiguous_matches("","a").value().empty());
require_case(wildcard_contiguous_matches("a","??").value().empty());
require_case(!wildcard_contiguous_matches("a",""));
return 0;
}
