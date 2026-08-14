#include "binary-crc-syndrome.cpp"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::crypto_square;
int main() {
require_case(binary_crc_syndrome("1101","1011")=="001");
require_case(binary_crc_syndrome("0","11")=="0");
require_case(!binary_crc_syndrome("","11"));
require_case(!binary_crc_syndrome("102","11"));
require_case(!binary_crc_syndrome("1","10"));
return 0;
}
