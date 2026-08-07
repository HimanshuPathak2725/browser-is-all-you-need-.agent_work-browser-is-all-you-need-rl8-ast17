# Weekly window intersection

Implement the C++17 task in `weekly-window-intersection.cpp`. Intersect recurring half-open weekly-minute windows. A begin greater than end wraps across the week boundary; return sorted non-touching segments.

The exact public API is:

```cpp
namespace charm::clockwork { struct Window { int begin; int end; }; std::vector<Window> intersect_weekly(Window,Window); }
```

Required edge behavior:

- touching windows have empty intersection
- wraparound may split
- equal endpoints denote empty
- out-of-range endpoints are invalid
- output is normalized and sorted

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
