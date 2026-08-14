#include "ragged-columnar-transpose.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::crypto_square;
int main() {
CHECK(ragged_columnar_transpose("abcdefg",3,{2,0,1})=="cfadgbe");
CHECK(ragged_columnar_transpose("",2,{0,1})=="");
CHECK(ragged_columnar_transpose("a",1,{0})=="a");
CHECK(!ragged_columnar_transpose("x",0,{}));
CHECK(!ragged_columnar_transpose("x",2,{0,0}));
return 0;
}
