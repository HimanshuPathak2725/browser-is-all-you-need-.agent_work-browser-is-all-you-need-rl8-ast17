# Ordered adjacency permutation solver

Implement the C++17 task in `ordered-adjacency-permutation-solver.cpp`. Solve a permutation of distinct labels subject to before and adjacent constraints. Return the lexically smallest satisfying left-to-right order. All labels and constraint endpoints must exist, labels are limited to eight, and self-constraints reject. Return an empty inner optional when a valid problem has no solution.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::zebra_puzzle {
struct OrderClue { std::string before; std::string after; }; struct AdjacentClue { std::string first; std::string second; };
std::optional<std::optional<std::vector<std::string>>> solve_ordered_adjacency(const std::vector<std::string>& labels, const std::vector<OrderClue>& orders, const std::vector<AdjacentClue>& adjacent);
}
```

Required edge behavior:

- outer optional validates problem
- inner optional reports satisfiability
- lexically smallest solution wins
- label count is bounded
- constraints use known distinct labels

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
