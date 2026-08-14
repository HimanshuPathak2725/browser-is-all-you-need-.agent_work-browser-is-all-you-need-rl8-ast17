#include "selected-dft-bins.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::complex_numbers;
int main() {
auto d=selected_dft_bins({{1,0},{1,0}}, {0,1}).value();CHECK(std::abs(d[0]-std::complex<double>{2,0})<1e-9);CHECK(std::abs(d[1])<1e-9);
CHECK(selected_dft_bins({{3,4}},{}).value().empty());
CHECK(!selected_dft_bins({},{}));
CHECK(!selected_dft_bins({{1,0}},{1}));
CHECK(!selected_dft_bins({{1,0}},{0,0}));
return 0;
}
