#include "hermitian-energy.hpp"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::complex_numbers;
int main() {
CHECK(std::abs(hermitian_quadratic_energy({{{2,0},{0,0}},{{0,0},{3,0}}},{{1,0},{2,0}},1e-9).value()-14)<1e-9);
CHECK(hermitian_quadratic_energy({}, {},0)==0);
CHECK(!hermitian_quadratic_energy({{{1,0},{1,0}},{{0,0},{1,0}}},{{1,0},{1,0}},0));
CHECK(!hermitian_quadratic_energy({}, {},-1));
CHECK(!hermitian_quadratic_energy({{{1,0}}},{},0));
return 0;
}
