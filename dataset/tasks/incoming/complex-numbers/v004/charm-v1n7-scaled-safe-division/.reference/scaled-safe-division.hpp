#pragma once

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

std::optional<std::complex<double>> divide_complex_scaled(std::complex<double> numerator, std::complex<double> denominator, double epsilon);
}

inline std::optional<std::complex<double>> charm::v1n7::complex_numbers::divide_complex_scaled(std::complex<double> numerator,std::complex<double> denominator,double epsilon){auto finite=[](std::complex<double> z){return std::isfinite(z.real())&&std::isfinite(z.imag());};if(epsilon<0||!std::isfinite(epsilon)||!finite(numerator)||!finite(denominator)||std::abs(denominator)<=epsilon)return std::nullopt;auto value=numerator/denominator;if(!finite(value))return std::nullopt;return value;}
