# Allergen rule evaluator

Implement the C++17 task in `allergen-rule-evaluator.h`, `allergen-rule-evaluator.cpp`, `allergen-rule-evaluator_detail.cpp`. Evaluate a fully parenthesized boolean rule over allergen labels. Leaves are nonempty lowercase identifiers; operators are !, &, and |. Whitespace is ignored and malformed syntax rejects.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::allergies {
std::optional<bool> evaluate_allergen_rule(std::string_view expression, const std::set<std::string>& present);
}
```

Required edge behavior:

- identifiers are lowercase ASCII
- binary operators require parentheses
- negation binds one expression
- trailing input rejects
- membership is exact

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
