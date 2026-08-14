#include "lfsr-cycle-report.hpp"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::crypto_square;
int main() {
require_case(lfsr_cycle_report("1",{0}).value()==std::pair<std::size_t,std::size_t>{0,1});
require_case(lfsr_cycle_report("00",{0}).value()==std::pair<std::size_t,std::size_t>{0,1});
require_case(lfsr_cycle_report("10",{0,1}).value().second>0);
require_case(!lfsr_cycle_report("",{0}));
require_case(!lfsr_cycle_report("10",{2}));
return 0;
}
