#include "bezier-complex-samples.cpp"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::complex_numbers;
int main() {
auto b=sample_complex_bezier({{0,0},{2,2}},{{0,1},{1,2},{1,1}}).value();CHECK(std::abs(b[1]-std::complex<double>{1,1})<1e-9);
CHECK(std::abs(b.front())<1e-9);CHECK(std::abs(b.back()-std::complex<double>{2,2})<1e-9);
CHECK(sample_complex_bezier({{4,1}},{}).value().empty());
CHECK(!sample_complex_bezier({},{}));
CHECK(!sample_complex_bezier({{0,0}},{{2,1}}));
return 0;
}
