#pragma once
#include <cstdlib>
#include <utility>
#include <vector>
namespace charm::diamond {
struct Rect { int x0; int y0; int x1; int y1; };
inline std::vector<std::pair<int,int>> clipped_cells(int center_x, int center_y, int radius, Rect view) {
    if (radius < 0 || view.x0 > view.x1 || view.y0 > view.y1) return {};
    std::vector<std::pair<int,int>> out;
    for (int y = view.y0; y < view.y1; ++y)
        for (int x = view.x0; x < view.x1; ++x)
            if (std::abs(static_cast<long long>(x) - center_x) + std::abs(static_cast<long long>(y) - center_y) <= radius)
                out.push_back({x - view.x0, y - view.y0});
    return out;
}
}
