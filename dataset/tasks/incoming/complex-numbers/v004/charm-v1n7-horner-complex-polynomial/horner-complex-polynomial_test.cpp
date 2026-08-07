#include "horner-complex-polynomial.cpp"

#include <cassert>

using charm::v1n7::complex_numbers::evaluate_complex_polynomial;
int main() {
    using C=std::complex<double>;assert((evaluate_complex_polynomial({C{1,0},C{0,0},C{-1,0}},C{2,0})==C{3,0}));
    assert((evaluate_complex_polynomial({},C{9,2})==C{0,0}));
    assert((evaluate_complex_polynomial({C{0,1}},C{2,3})==C{0,1}));
    assert(!evaluate_complex_polynomial({C{std::numeric_limits<double>::infinity(),0}},C{0,0}));
    assert(!evaluate_complex_polynomial({},C{std::numeric_limits<double>::quiet_NaN(),0}));
    return 0;
}
