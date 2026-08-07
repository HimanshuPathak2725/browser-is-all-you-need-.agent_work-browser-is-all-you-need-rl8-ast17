#include <algorithm>
#include <array>
#include <climits>
#include <cstdlib>
#include <future>
#include <cmath>
#include <complex>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <functional>
#include <limits>
#include <map>
#include <memory>
#include <numeric>
#include <optional>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace charm::v1n7::complex_numbers {

std::optional<std::complex<double>> evaluate_complex_polynomial(const std::vector<std::complex<double>>& coefficients, std::complex<double> point);
}

std::optional<std::complex<double>> charm::v1n7::complex_numbers::evaluate_complex_polynomial(const std::vector<std::complex<double>>& coefficients,std::complex<double> point){auto finite=[](std::complex<double> z){return std::isfinite(z.real())&&std::isfinite(z.imag());};if(!finite(point)||std::any_of(coefficients.begin(),coefficients.end(),[&](auto z){return !finite(z);}))return std::nullopt;std::complex<double> value{0.0,0.0};for(auto coefficient:coefficients)value=value*point+coefficient;if(!finite(value))return std::nullopt;return value;}
