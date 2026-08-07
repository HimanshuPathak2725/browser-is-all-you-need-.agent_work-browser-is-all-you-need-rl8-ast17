#include "encapsulated-complex-value.h"

#include <cassert>

using namespace charm::v1n7::complex_numbers;
int main() {
    auto z=make_encapsulated_complex(3.0,4.0);assert(z.real()==3.0&&z.imag()==4.0&&z.magnitude_squared()==25.0);
    assert(z.conjugate()==make_encapsulated_complex(3.0,-4.0));
    assert(make_encapsulated_complex(0.0,0.0).magnitude_squared()==0.0);
    assert(!(z==make_encapsulated_complex(3.0,5.0)));
    assert(make_encapsulated_complex(-2.0,1.5).conjugate()==make_encapsulated_complex(-2.0,-1.5));
    return 0;
}
