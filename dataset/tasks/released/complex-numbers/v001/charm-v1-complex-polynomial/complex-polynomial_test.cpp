#include "complex-polynomial.cpp"
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
