#pragma once

#include <algorithm>
#include <array>
#include <cctype>
#include <climits>
#include <cstdlib>
#include <future>
#include <cmath>
#include <complex>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <functional>
#include <iterator>
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

namespace charm::v1r87_37414::complex_numbers {

std::optional<double> hermitian_quadratic_energy(const std::vector<std::vector<std::complex<double>>>& matrix, const std::vector<std::complex<double>>& x, double tolerance);
}

namespace charm::v1r87_37414::complex_numbers {
inline std::optional<double> hermitian_quadratic_energy(const std::vector<std::vector<std::complex<double>>>& matrix, const std::vector<std::complex<double>>& x, double tolerance) {
if(tolerance<0||matrix.size()!=x.size())return std::nullopt;
std::size_t n=x.size();
for(const auto&r:matrix)if(r.size()!=n)return std::nullopt;
for(std::size_t i=0;i<n;++i)for(std::size_t j=0;j<n;++j)if(std::abs(matrix[i][j]-std::conj(matrix[j][i]))>tolerance)return std::nullopt;
std::complex<double> e{};
for(std::size_t i=0;i<n;++i)for(std::size_t j=0;j<n;++j)e+=std::conj(x[i])*matrix[i][j]*x[j];
if(std::abs(e.imag())>tolerance)return std::nullopt;
return e.real();

}
}
