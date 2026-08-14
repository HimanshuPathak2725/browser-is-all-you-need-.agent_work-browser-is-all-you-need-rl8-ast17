#include "parallel-caesar-coincidences.cpp"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::parallel_letter_frequency;
int main() {
auto c=parallel_caesar_coincidences("abc","bcd",4).value();CHECK(c[1]==3&&c[0]==0);
CHECK(parallel_caesar_coincidences("","",1).value()[0]==0);
CHECK(parallel_caesar_coincidences("z","a",30).value()[1]==1);
CHECK(!parallel_caesar_coincidences("a","aa",1));
CHECK(!parallel_caesar_coincidences("A","a",1));
return 0;
}
