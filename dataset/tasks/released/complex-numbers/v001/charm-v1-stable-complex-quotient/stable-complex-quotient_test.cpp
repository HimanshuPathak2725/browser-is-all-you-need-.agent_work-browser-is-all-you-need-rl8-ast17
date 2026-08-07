#include "stable-complex-quotient.h"
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
    assert(StableComplex(1, 1).near(StableComplex(1.000001, 1), 1e-5, 0));
    assert(!StableComplex(1, 1).near(StableComplex(2, 1), -1, 1));
    assert(!StableComplex(std::numeric_limits<double>::infinity(), 0).near(StableComplex(), 1, 1));
    return 0;
}
