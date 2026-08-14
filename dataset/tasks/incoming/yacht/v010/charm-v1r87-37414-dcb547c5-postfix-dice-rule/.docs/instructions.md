# Postfix dice rule

Implement the C++17 task in `postfix-dice-rule.h`, `postfix-dice-rule.cpp`. Evaluate a postfix dice scoring program. Tokens are sum, max, count:N for face N in [1,6], nonnegative integer literals, and binary + or *. Dice faces must be 1 through 6; malformed stacks and checked arithmetic reject.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::yacht {
std::optional<std::int64_t> evaluate_postfix_dice_rule(const std::vector<int>& dice, const std::vector<std::string>& program);
}
```

Required edge behavior:

- dice faces are 1 through 6
- program is postfix
- count syntax is exact
- max needs at least one die
- arithmetic and final stack shape are checked

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
