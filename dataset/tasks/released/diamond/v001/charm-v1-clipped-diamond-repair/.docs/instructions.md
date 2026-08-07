# Clipped filled diamond

Implement the C++17 task in `clipped-diamond-repair.hpp`. Clip a filled Manhattan diamond to a half-open viewport and return occupied positions row-major relative to the viewport origin.

The exact public API is:

```cpp
namespace charm::diamond { struct Rect { int x0; int y0; int x1; int y1; }; std::vector<std::pair<int,int>> clipped_cells(int,int,int,Rect); }
```

Required edge behavior:

- negative radius rejects
- reversed viewport rejects
- empty viewport
- diamond boundary is included
- coordinates are viewport-relative

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
