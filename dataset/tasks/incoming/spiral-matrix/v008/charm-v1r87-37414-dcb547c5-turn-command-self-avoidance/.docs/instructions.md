# Turn command self avoidance

Implement the C++17 task in `turn-command-self-avoidance.cpp`. Replay commands L, R, and F from origin facing north. Turns rotate in place; F advances one lattice step. Return every visited position including origin, or reject the first repeated position or invalid command.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::spiral_matrix {
using GridPoint = std::pair<int,int>;
std::optional<std::vector<GridPoint>> replay_self_avoiding_turns(std::string_view commands);
}
```

Required edge behavior:

- origin is included
- turns do not visit a new point
- movement is unit cardinal
- repeated positions reject
- invalid commands reject

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
