# String rule score

Implement the C++17 task in `string-rule-score.h`, `string-rule-score.cpp`. Score exactly five six-sided dice under a string rule. Supported case-sensitive rules are sum, all-even, three-match, and full-run. sum totals all dice; all-even scores the sum only if every die is even; three-match scores the sum when any face occurs at least three times; full-run scores 30 for 1-5 or 2-6. Unknown rules or invalid dice reject.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::yacht {
std::optional<int> score_string_rule(std::string_view rule, const std::array<int,5>& dice);
}
```

Required edge behavior:

- category representation is string
- rules are case-sensitive
- unknown rules reject
- all dice are validated
- rule boundaries are exhaustive

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
