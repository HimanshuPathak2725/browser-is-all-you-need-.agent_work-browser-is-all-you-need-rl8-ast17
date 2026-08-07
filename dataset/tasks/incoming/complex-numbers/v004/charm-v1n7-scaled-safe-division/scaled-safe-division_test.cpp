#include "scaled-safe-division.hpp"

#include <cassert>

using charm::v1n7::complex_numbers::divide_complex_scaled;
int main() {
    using C=std::complex<double>;auto r=divide_complex_scaled(C{3,1},C{1,-1},0.0);assert(r&&std::abs(*r-C{1,2})<1e-12);
    assert(!divide_complex_scaled(C{1,0},C{0,0},0.0));
    assert(!divide_complex_scaled(C{1,0},C{1,0},-1.0));
    assert((divide_complex_scaled(C{0,0},C{2,0},0.0)==C{0,0}));
    assert(!divide_complex_scaled(C{1,0},C{0.001,0},0.01));
    return 0;
}
