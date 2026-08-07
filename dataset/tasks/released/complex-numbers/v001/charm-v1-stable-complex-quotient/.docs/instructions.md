# Stable complex quotient

Implement the C++17 task in `stable-complex-quotient.h`, `stable-complex-quotient.cpp`, `stable-complex-quotient_detail.cpp`. Implement finite rectangular complex arithmetic, a scale-safe quotient, and combined absolute/relative approximate equality.

The exact public API is:

```cpp
namespace charm::complex { class StableComplex { public: StableComplex(double=0,double=0); double real() const; double imag() const; StableComplex operator+(StableComplex) const; std::optional<StableComplex> divided_by(StableComplex) const; bool near(StableComplex,double,double) const; }; }
```

Required edge behavior:

- division by zero returns nullopt
- non-finite operands reject
- very large balanced operands avoid overflow
- negative tolerances reject
- absolute and relative tolerance are combined

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
