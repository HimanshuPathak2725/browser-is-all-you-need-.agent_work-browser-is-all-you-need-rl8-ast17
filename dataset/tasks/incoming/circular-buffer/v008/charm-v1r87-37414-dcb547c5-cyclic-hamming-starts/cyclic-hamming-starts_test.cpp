#include "cyclic-hamming-starts.cpp"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::circular_buffer;
int main() {
require_case(cyclic_hamming_starts("abc","cab",0).value()==std::vector<std::size_t>{2});
require_case(cyclic_hamming_starts("ab","ababa",0).value()==std::vector<std::size_t>{0});
require_case(cyclic_hamming_starts("abc","acc",1).value()==std::vector<std::size_t>{0});
require_case(cyclic_hamming_starts("aa","b",1).value()==(std::vector<std::size_t>{0,1}));
require_case(!cyclic_hamming_starts("","x",0));
return 0;
}
