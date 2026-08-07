"""Owner source for the three CHARM V1 Complex Numbers tasks."""

from __future__ import annotations

from scripts.charm_v1_topics.common import package, prompt, support


STABLE = r'''#pragma once
#include <algorithm>
#include <cmath>
#include <optional>
namespace charm::complex {
class StableComplex {
public:
    StableComplex(double real = 0.0, double imag = 0.0) : real_(real), imag_(imag) {}
    double real() const { return real_; }
    double imag() const { return imag_; }
    StableComplex operator+(StableComplex other) const { return {real_ + other.real_, imag_ + other.imag_}; }
    std::optional<StableComplex> divided_by(StableComplex divisor) const {
        if (!finite() || !divisor.finite() || (divisor.real_ == 0.0 && divisor.imag_ == 0.0)) return std::nullopt;
        const double scale = std::max(std::abs(divisor.real_), std::abs(divisor.imag_));
        const double scaled_real = divisor.real_ / scale;
        const double scaled_imag = divisor.imag_ / scale;
        const double denominator =
            scaled_real * scaled_real + scaled_imag * scaled_imag;
        const double numerator_real = real_ / scale;
        const double numerator_imag = imag_ / scale;
        const double real =
            (numerator_real * scaled_real + numerator_imag * scaled_imag) / denominator;
        const double imag =
            (numerator_imag * scaled_real - numerator_real * scaled_imag) / denominator;
        if (!std::isfinite(real) || !std::isfinite(imag)) return std::nullopt;
        return StableComplex(real, imag);
    }
    bool near(StableComplex other, double absolute_tolerance, double relative_tolerance) const {
        if (!finite() || !other.finite() || absolute_tolerance < 0 || relative_tolerance < 0) return false;
        const double distance = std::hypot(real_ - other.real_, imag_ - other.imag_);
        const double scale = std::max(std::hypot(real_, imag_), std::hypot(other.real_, other.imag_));
        return distance <= absolute_tolerance + relative_tolerance * scale;
    }
private:
    bool finite() const { return std::isfinite(real_) && std::isfinite(imag_); }
    double real_;
    double imag_;
};
}
'''
STABLE_TEST = r'''#include "stable-complex-quotient.h"
#include <cassert>
#include <cmath>
#include <limits>
using charm::complex::StableComplex;
int main() {
    const StableComplex sum = StableComplex(1, 2) + StableComplex(3, -5);
    assert(sum.real() == 4 && sum.imag() == -3);
    const auto quotient = StableComplex(3, 4).divided_by(StableComplex(1, -2));
    assert(quotient && quotient->near(StableComplex(-1, 2), 1e-12, 1e-12));
    assert(!StableComplex(1, 1).divided_by(StableComplex()));
    const auto scaled = StableComplex(1e300, 1e300).divided_by(StableComplex(1e300, -1e300));
    assert(scaled && scaled->near(StableComplex(0, 1), 1e-12, 1e-12));
    const double maximum = std::numeric_limits<double>::max();
    const auto balanced = StableComplex(maximum, maximum).divided_by(
        StableComplex(maximum, maximum));
    assert(balanced && balanced->near(StableComplex(1, 0), 1e-12, 1e-12));
    assert(StableComplex(1, 1).near(StableComplex(1.000001, 1), 1e-5, 0));
    assert(!StableComplex(1, 1).near(StableComplex(2, 1), -1, 1));
    assert(!StableComplex(std::numeric_limits<double>::infinity(), 0).near(StableComplex(), 1, 1));
    return 0;
}
'''


POLYNOMIAL = r'''#include <complex>
#include <vector>
namespace charm::complex {
struct PairValue { std::complex<double> value; std::complex<double> derivative; };
inline PairValue evaluate_with_derivative(
    const std::vector<std::complex<double>>& descending,
    std::complex<double> point) {
    PairValue result{{0.0, 0.0}, {0.0, 0.0}};
    for (const auto coefficient : descending) {
        result.derivative = result.derivative * point + result.value;
        result.value = result.value * point + coefficient;
    }
    return result;
}
}
'''
POLYNOMIAL_START = POLYNOMIAL.replace("result.derivative = result.derivative * point + result.value;", "result.derivative = result.derivative * point + coefficient;")
POLYNOMIAL_TEST = r'''#include "complex-polynomial.cpp"
#include <cassert>
#include <complex>
#include <vector>
using charm::complex::evaluate_with_derivative;
int main() {
    const auto empty = evaluate_with_derivative({}, {2, 1});
    assert(empty.value == std::complex<double>(0, 0) && empty.derivative == std::complex<double>(0, 0));
    const auto constant = evaluate_with_derivative({{5, -2}}, {9, 9});
    assert(constant.value == std::complex<double>(5, -2) && constant.derivative == std::complex<double>(0, 0));
    const auto quadratic = evaluate_with_derivative({{1, 0}, {2, 0}, {3, 0}}, {2, 0});
    assert(quadratic.value == std::complex<double>(11, 0));
    assert(quadratic.derivative == std::complex<double>(6, 0));
    const auto complex_value = evaluate_with_derivative({{1, 0}, {0, 0}}, {0, 1});
    assert(complex_value.value == std::complex<double>(0, 1));
    assert(complex_value.derivative == std::complex<double>(1, 0));
    const auto zero = evaluate_with_derivative({{2, 1}, {-3, 4}}, {0, 0});
    assert(zero.value == std::complex<double>(-3, 4) && zero.derivative == std::complex<double>(2, 1));
    return 0;
}
'''


POLAR = r'''#pragma once
#include <cmath>
#include <complex>
#include <optional>
#include <utility>
#include <vector>
namespace charm::complex {
inline std::optional<double> weighted_direction(
    const std::vector<std::pair<std::complex<double>, double>>& phasors) {
    std::complex<long double> sum(0.0L, 0.0L);
    for (const auto& item : phasors) {
        const auto value = item.first;
        const double weight = item.second;
        if (weight < 0 || !std::isfinite(weight) || !std::isfinite(value.real()) || !std::isfinite(value.imag())) return std::nullopt;
        const double scale = std::max(std::abs(value.real()), std::abs(value.imag()));
        if (scale != 0.0 && weight != 0.0) {
            const long double scaled_real =
                static_cast<long double>(value.real()) / scale;
            const long double scaled_imag =
                static_cast<long double>(value.imag()) / scale;
            const long double magnitude = std::hypot(scaled_real, scaled_imag);
            sum += static_cast<long double>(weight) *
                   std::complex<long double>(scaled_real / magnitude, scaled_imag / magnitude);
        }
    }
    if (sum.real() == 0.0L && sum.imag() == 0.0L) return std::nullopt;
    long double angle = std::atan2(sum.imag(), sum.real());
    if (angle < 0) angle += 2.0L * std::acos(-1.0L);
    return static_cast<double>(angle);
}
}
'''
POLAR_START = r'''#pragma once
#include <complex>
#include <optional>
#include <utility>
#include <vector>
namespace charm::complex {
std::optional<double> weighted_direction(const std::vector<std::pair<std::complex<double>, double>>& phasors);
}
'''
POLAR_TEST = r'''#include "polar-mean-repair.hpp"
#include <cassert>
#include <cmath>
#include <complex>
#include <limits>
#include <vector>
using charm::complex::weighted_direction;
int main() {
    assert(!weighted_direction({}));
    const auto east = weighted_direction({{{3, 0}, 2}});
    assert(east && std::abs(*east) < 1e-12);
    const auto north = weighted_direction({{{0, 2}, 5}, {{2, 0}, 0}});
    assert(north && std::abs(*north - std::acos(-1.0) / 2) < 1e-12);
    assert(!weighted_direction({{{1, 0}, 1}, {{-1, 0}, 1}}));
    assert(!weighted_direction({{{1, 0}, -1}}));
    const auto southwest = weighted_direction({{{-1, -1}, 2}});
    assert(southwest && *southwest > std::acos(-1.0));
    assert(!weighted_direction({{{0, 0}, 9}}));
    const double maximum = std::numeric_limits<double>::max();
    const auto diagonal = weighted_direction({{{maximum, maximum}, 1}});
    assert(diagonal &&
           std::abs(*diagonal - std::acos(-1.0) / 4) < 1e-12);
    return 0;
}
'''


def tasks() -> list[dict]:
    stable = ["stable-complex-quotient.h", "stable-complex-quotient.cpp", "stable-complex-quotient_detail.cpp"]
    poly = ["complex-polynomial.cpp"]
    polar = ["polar-mean-repair.hpp"]
    return [
        package(topic="Complex Numbers", task_id="charm-v1-stable-complex-quotient", instructions=prompt("Stable complex quotient", "Implement finite rectangular complex arithmetic, a scale-safe quotient, and combined absolute/relative approximate equality.", "namespace charm::complex { class StableComplex { public: StableComplex(double=0,double=0); double real() const; double imag() const; StableComplex operator+(StableComplex) const; std::optional<StableComplex> divided_by(StableComplex) const; bool near(StableComplex,double,double) const; }; }", ["division by zero returns nullopt", "non-finite operands reject", "very large balanced operands avoid overflow", "negative tolerances reject", "absolute and relative tolerance are combined"], stable), editable={stable[0]: "#pragma once\nnamespace charm::complex { class StableComplex {}; }\n", stable[1]: support(stable[0], 51), stable[2]: support(stable[0], 52)}, reference={stable[0]: STABLE, stable[1]: support(stable[0], 53), stable[2]: support(stable[0], 54)}, hidden_name="stable-complex-quotient_test.cpp", hidden=STABLE_TEST, category="stable-arithmetic", tags=["boundary", "floating-point", "division", "header-extension"]),
        package(topic="Complex Numbers", task_id="charm-v1-complex-polynomial", instructions=prompt("Complex polynomial and derivative", "Evaluate descending complex coefficients and the derivative together in one Horner pass.", "namespace charm::complex { struct PairValue { std::complex<double> value; std::complex<double> derivative; }; PairValue evaluate_with_derivative(const std::vector<std::complex<double>>&,std::complex<double>); }", ["empty polynomial is zero", "constant derivative is zero", "descending coefficient order", "complex evaluation point", "point zero exposes final coefficients"], poly), editable={poly[0]: POLYNOMIAL_START}, reference={poly[0]: POLYNOMIAL}, hidden_name="complex-polynomial_test.cpp", hidden=POLYNOMIAL_TEST, category="horner-derivative", tags=["semantic-bug", "complex", "one-pass", "cpp-only"]),
        package(topic="Complex Numbers", task_id="charm-v1-polar-mean-repair", instructions=prompt("Weighted phasor direction", "Compute the mean direction of normalized complex phasors weighted by nonnegative finite weights; return an angle in [0,2pi).", "namespace charm::complex { std::optional<double> weighted_direction(const std::vector<std::pair<std::complex<double>,double>>&); }", ["negative or non-finite weights invalidate", "zero weights contribute nothing", "zero-magnitude phasors contribute nothing", "zero resultant has no direction", "negative atan2 results wrap into [0,2pi)"], polar), editable={polar[0]: POLAR_START}, reference={polar[0]: POLAR}, hidden_name="polar-mean-repair_test.cpp", hidden=POLAR_TEST, category="circular-statistics", tags=["header-only", "weighted", "normalization", "optional"]),
    ]
