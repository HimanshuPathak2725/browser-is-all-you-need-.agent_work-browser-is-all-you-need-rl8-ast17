#include "parallel-caesar-coincidences.cpp"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::parallel_letter_frequency;
int main() {
auto c=parallel_caesar_coincidences("abc","bcd",4).value();require_case(c[1]==3&&c[0]==0);
require_case(parallel_caesar_coincidences("","",1).value()[0]==0);
require_case(parallel_caesar_coincidences("z","a",30).value()[1]==1);
require_case(!parallel_caesar_coincidences("a","aa",1));
require_case(!parallel_caesar_coincidences("A","a",1));
return 0;
}
