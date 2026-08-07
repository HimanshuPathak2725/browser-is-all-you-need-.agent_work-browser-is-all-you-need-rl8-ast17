# Manhattan shell

Implement the C++17 task in `manhattan-shell.cpp`. Enumerate every integer cell at an exact Manhattan radius clockwise from the top cell, without duplicate corner cells.

The exact public API is:

```cpp
namespace charm::diamond { struct Point { int x; int y; bool operator==(const Point&) const; }; std::vector<Point> shell(Point,int); }
```

Required edge behavior:

- negative radius is empty
- radius zero is the center
- positive shells contain exactly 4r cells
- first cell is top
- center offsets may be negative

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
