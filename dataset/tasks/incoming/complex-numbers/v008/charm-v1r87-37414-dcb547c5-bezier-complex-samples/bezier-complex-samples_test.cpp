#include "bezier-complex-samples.cpp"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::complex_numbers;
int main() {
auto b=sample_complex_bezier({{0,0},{2,2}},{{0,1},{1,2},{1,1}}).value();require_case(std::abs(b[1]-std::complex<double>{1,1})<1e-9);
require_case(std::abs(b.front())<1e-9);require_case(std::abs(b.back()-std::complex<double>{2,2})<1e-9);
require_case(sample_complex_bezier({{4,1}},{}).value().empty());
require_case(!sample_complex_bezier({},{}));
require_case(!sample_complex_bezier({{0,0}},{{2,1}}));
return 0;
}
