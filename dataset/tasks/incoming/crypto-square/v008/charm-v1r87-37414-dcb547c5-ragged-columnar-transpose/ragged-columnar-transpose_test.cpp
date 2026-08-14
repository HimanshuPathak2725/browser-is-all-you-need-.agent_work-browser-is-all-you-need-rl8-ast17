#include "ragged-columnar-transpose.h"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::crypto_square;
int main() {
require_case(ragged_columnar_transpose("abcdefg",3,{2,0,1})=="cfadgbe");
require_case(ragged_columnar_transpose("",2,{0,1})=="");
require_case(ragged_columnar_transpose("a",1,{0})=="a");
require_case(!ragged_columnar_transpose("x",0,{}));
require_case(!ragged_columnar_transpose("x",2,{0,0}));
return 0;
}
