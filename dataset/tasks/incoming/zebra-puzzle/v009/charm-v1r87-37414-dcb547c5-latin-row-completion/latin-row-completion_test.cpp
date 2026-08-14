#include "latin-row-completion.cpp"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::zebra_puzzle;
int main() {
CHECK(complete_unique_latin_row({{1,2},{0,0}},1).value()==std::vector<int>({2,1}));
CHECK(complete_unique_latin_row({{1}},0).value()==std::vector<int>{1});
CHECK(!complete_unique_latin_row({},0));
CHECK(!complete_unique_latin_row({{1,1},{0,0}},1));
CHECK(!complete_unique_latin_row({{1,2},{0}},1));
return 0;
}
