#include "hermitian-energy.hpp"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::complex_numbers;
int main() {
require_case(std::abs(hermitian_quadratic_energy({{{2,0},{0,0}},{{0,0},{3,0}}},{{1,0},{2,0}},1e-9).value()-14)<1e-9);
require_case(hermitian_quadratic_energy({}, {},0)==0);
require_case(!hermitian_quadratic_energy({{{1,0},{1,0}},{{0,0},{1,0}}},{{1,0},{1,0}},0));
require_case(!hermitian_quadratic_energy({}, {},-1));
require_case(!hermitian_quadratic_energy({{{1,0}}},{},0));
return 0;
}
