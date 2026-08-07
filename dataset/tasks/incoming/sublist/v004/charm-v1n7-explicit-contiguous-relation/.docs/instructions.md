# Explicit contiguous relation

Implement the C++17 task in `explicit-contiguous-relation.h`, `explicit-contiguous-relation.cpp`. Classify two integer sequences using the exact SequenceRelation enumerators. containment means contiguous occurrence. Equal sequences are equal; otherwise a contained first sequence is proper_sublist, a containing first sequence is proper_superlist, and neither is unrelated. Empty-sequence behavior follows these definitions. Complexity is O(n*m) or better.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::sublist {
enum class SequenceRelation { equal, proper_sublist, proper_superlist, unrelated };
SequenceRelation classify_contiguous_relation(const std::vector<int>& first, const std::vector<int>& second);
}
```

Required edge behavior:

- relation names are exact
- containment is contiguous
- equal precedes proper relations
- empty behavior is explicit
- repeated values use sequence equality

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
