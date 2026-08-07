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
class EncapsulatedComplex { public: EncapsulatedComplex(double real, double imag); double real() const; double imag() const; double magnitude_squared() const; EncapsulatedComplex conjugate() const; bool operator==(const EncapsulatedComplex& other) const; private: double real_; double imag_; };
EncapsulatedComplex make_encapsulated_complex(double real, double imag);
}
