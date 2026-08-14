#include "latin-row-completion.cpp"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::zebra_puzzle;
int main() {
require_case(complete_unique_latin_row({{1,2},{0,0}},1).value()==std::vector<int>({2,1}));
require_case(complete_unique_latin_row({{1}},0).value()==std::vector<int>{1});
require_case(!complete_unique_latin_row({},0));
require_case(!complete_unique_latin_row({{1,1},{0,0}},1));
require_case(!complete_unique_latin_row({{1,2},{0}},1));
return 0;
}
