#include "confirmed-rolling-hash-matches.cpp"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::sublist;
int main() {
CHECK(confirmed_rolling_hash_matches("ababa","aba",257).value()==std::vector<std::size_t>({0,2}));
CHECK(confirmed_rolling_hash_matches("aaa","a",3).value()==std::vector<std::size_t>({0,1,2}));
CHECK(confirmed_rolling_hash_matches("","a",3).value().empty());
CHECK(!confirmed_rolling_hash_matches("a","",3));
CHECK(!confirmed_rolling_hash_matches("a","a",2));
return 0;
}
