# Rotating sensitivity mask repair

Repair and complete the header-only C++17 type in
`rotating-sensitivity-mask.hpp`, in namespace `charm::allergy`.

Only the low eight bits of the constructor's `raw_mask` are retained. Normalize
the signed rotation into `[0, 7]`. The public allergen order is exactly:
`cedar, dust, egg, latex, mold, nickel, pollen, wool`. For allergen index `i`,
`reacts_to` tests stored bit `(i + normalized_rotation) % 8`. An unknown name
returns `false`. `reactions()` returns every reacting public name in that fixed
order.

Required API:

```cpp
class SensitivityMask {
public:
    SensitivityMask(unsigned raw_mask, int rotation);
    bool reacts_to(std::string_view allergen) const;
    std::vector<std::string> reactions() const;
};
```

The initial header intentionally does not compile. Preserve the exact API and
keep all definitions inline in the header. Use only the standard library.
