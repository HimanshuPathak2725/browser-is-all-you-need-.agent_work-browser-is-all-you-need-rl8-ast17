# Obstacle spiral walk

Implement the C++17 task in `obstacle-spiral-walk.cpp`. Starting facing right, visit unblocked cells, turning clockwise whenever the next cell is blocked, outside, or visited; stop after no legal neighbor remains.

The exact public API is:

```cpp
namespace charm::spiral { struct Cell { int row; int col; bool operator==(const Cell&) const; }; std::vector<Cell> walk(const std::vector<std::string>&,Cell); }
```

Required edge behavior:

- grid is nonempty rectangular
- only dot cells are walkable
- invalid or blocked start returns empty
- a cell is never revisited
- the walk may stop before disconnected cells

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
