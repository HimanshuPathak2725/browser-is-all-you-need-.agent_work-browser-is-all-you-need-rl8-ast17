# Encapsulated complex value

Implement the C++17 task in `encapsulated-complex-value.h`, `encapsulated-complex-value.cpp`, `encapsulated-complex-value_detail.cpp`. Construct an EncapsulatedComplex through make_encapsulated_complex. Its representation remains private; public real, imag, magnitude_squared, conjugate, and equality operations define all observable behavior.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::complex_numbers {
class EncapsulatedComplex { public: EncapsulatedComplex(double real, double imag); double real() const; double imag() const; double magnitude_squared() const; EncapsulatedComplex conjugate() const; bool operator==(const EncapsulatedComplex& other) const; private: double real_; double imag_; };
EncapsulatedComplex make_encapsulated_complex(double real, double imag);
}
```

Required edge behavior:

- representation is private
- accessors are const
- conjugation flips only imaginary sign
- magnitude is squared without a root
- equality is exact

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
