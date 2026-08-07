# Reserve-commit ring

Implement the C++17 task in `reserve-commit-ring.cpp`. Reserve capacity with monotonic tokens, commit or cancel once, and pop committed values in reservation order without skipping a pending head.

The exact public API is:

```cpp
namespace charm::ring { class CommitRing { public: explicit CommitRing(std::size_t); std::optional<std::size_t> reserve(); bool commit(std::size_t,int); bool cancel(std::size_t); std::optional<int> pop(); }; }
```

Required edge behavior:

- capacity includes pending entries
- out-of-order commit waits
- cancellation unblocks the head
- tokens are single-use
- empty pop returns nullopt

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
