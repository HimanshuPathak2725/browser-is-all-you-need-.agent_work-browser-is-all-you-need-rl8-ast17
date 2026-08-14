#include "lfsr-cycle-report.hpp"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::crypto_square;
int main() {
CHECK(lfsr_cycle_report("1",{0}).value()==std::pair<std::size_t,std::size_t>{0,1});
CHECK(lfsr_cycle_report("00",{0}).value()==std::pair<std::size_t,std::size_t>{0,1});
CHECK(lfsr_cycle_report("10",{0,1}).value().second>0);
CHECK(!lfsr_cycle_report("",{0}));
CHECK(!lfsr_cycle_report("10",{2}));
return 0;
}
