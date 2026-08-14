#include "binary-crc-syndrome.cpp"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::crypto_square;
int main() {
CHECK(binary_crc_syndrome("1101","1011")=="001");
CHECK(binary_crc_syndrome("0","11")=="0");
CHECK(!binary_crc_syndrome("","11"));
CHECK(!binary_crc_syndrome("102","11"));
CHECK(!binary_crc_syndrome("1","10"));
return 0;
}
