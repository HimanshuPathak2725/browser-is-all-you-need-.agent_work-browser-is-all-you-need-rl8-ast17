#include "confirmed-rolling-hash-matches.cpp"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::sublist;
int main() {
require_case(confirmed_rolling_hash_matches("ababa","aba",257).value()==std::vector<std::size_t>({0,2}));
require_case(confirmed_rolling_hash_matches("aaa","a",3).value()==std::vector<std::size_t>({0,1,2}));
require_case(confirmed_rolling_hash_matches("","a",3).value().empty());
require_case(!confirmed_rolling_hash_matches("a","",3));
require_case(!confirmed_rolling_hash_matches("a","a",2));
return 0;
}
