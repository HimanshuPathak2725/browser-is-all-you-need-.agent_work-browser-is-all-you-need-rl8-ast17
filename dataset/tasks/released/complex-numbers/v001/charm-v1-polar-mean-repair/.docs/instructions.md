# Weighted phasor direction

Implement the C++17 task in `polar-mean-repair.hpp`. Compute the mean direction of normalized complex phasors weighted by nonnegative finite weights; return an angle in [0,2pi).

The exact public API is:

```cpp
namespace charm::complex { std::optional<double> weighted_direction(const std::vector<std::pair<std::complex<double>,double>>&); }
```

Required edge behavior:

- negative or non-finite weights invalidate
- zero weights contribute nothing
- zero-magnitude phasors contribute nothing
- zero resultant has no direction
- negative atan2 results wrap into [0,2pi)

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
