# Unique score sheet

Implement the C++17 task in `unique-score-sheet.h`, `unique-score-sheet.cpp`. Score a sheet of named turns. Each row supplies one of the four supported string rules and five dice; a rule may appear at most once. Invalid rows reject the entire sheet. Return total score, number of used rules, and count of zero-scoring rows.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::yacht {
struct YachtTurn { std::string rule; std::array<int,5> dice; };
std::optional<std::array<int,3>> summarize_unique_score_sheet(const std::vector<YachtTurn>& turns);
}
```

Required edge behavior:

- each rule is used once
- unknown categories reject
- invalid dice reject
- zero scores are counted
- empty sheet summarizes to zeros

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
