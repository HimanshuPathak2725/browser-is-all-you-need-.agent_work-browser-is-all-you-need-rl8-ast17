# Complex polynomial and derivative

Implement the C++17 task in `complex-polynomial.cpp`. Evaluate descending complex coefficients and the derivative together in one Horner pass.

The exact public API is:

```cpp
namespace charm::complex { struct PairValue { std::complex<double> value; std::complex<double> derivative; }; PairValue evaluate_with_derivative(const std::vector<std::complex<double>>&,std::complex<double>); }
```

Required edge behavior:

- empty polynomial is zero
- constant derivative is zero
- descending coefficient order
- complex evaluation point
- point zero exposes final coefficients

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
