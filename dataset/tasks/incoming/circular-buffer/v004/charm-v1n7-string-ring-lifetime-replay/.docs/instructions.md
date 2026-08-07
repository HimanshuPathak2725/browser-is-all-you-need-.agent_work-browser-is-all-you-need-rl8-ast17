# String ring lifetime replay

Implement the C++17 task in `string-ring-lifetime-replay.h`, `string-ring-lifetime-replay.cpp`, `string-ring-lifetime-replay_detail.cpp`. Replay push, pop, and clear operations on a fixed-capacity ring of std::string values. Push on full either overwrites the oldest value or rejects according to the explicit mode; pop on empty rejects. Capacity zero is valid only for traces containing clear operations. Return the final logical order and pop history.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::circular_buffer {
enum class RingOpKind { push, pop, clear }; struct RingOp { RingOpKind kind; std::string value; }; struct RingReplay { std::vector<std::string> remaining; std::vector<std::string> popped; };
std::optional<RingReplay> replay_string_ring(std::size_t capacity, bool overwrite, const std::vector<RingOp>& operations);
}
```

Required edge behavior:

- strings exercise nontrivial lifetime
- overwrite removes oldest
- pop history is ordered
- zero capacity is explicit
- operation payloads are validated

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
