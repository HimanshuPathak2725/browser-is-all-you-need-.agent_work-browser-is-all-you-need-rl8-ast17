#include "cyclic-hamming-starts.cpp"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::circular_buffer;
int main() {
CHECK(cyclic_hamming_starts("abc","cab",0).value()==std::vector<std::size_t>{2});
CHECK(cyclic_hamming_starts("ab","ababa",0).value()==std::vector<std::size_t>{0});
CHECK(cyclic_hamming_starts("abc","acc",1).value()==std::vector<std::size_t>{0});
CHECK(cyclic_hamming_starts("aa","b",1).value()==(std::vector<std::size_t>{0,1}));
CHECK(!cyclic_hamming_starts("","x",0));
return 0;
}
