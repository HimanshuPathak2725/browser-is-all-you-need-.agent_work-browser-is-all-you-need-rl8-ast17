#include "selected-dft-bins.h"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::complex_numbers;
int main() {
auto d=selected_dft_bins({{1,0},{1,0}}, {0,1}).value();require_case(std::abs(d[0]-std::complex<double>{2,0})<1e-9);require_case(std::abs(d[1])<1e-9);
require_case(selected_dft_bins({{3,4}},{}).value().empty());
require_case(!selected_dft_bins({},{}));
require_case(!selected_dft_bins({{1,0}},{1}));
require_case(!selected_dft_bins({{1,0}},{0,0}));
return 0;
}
