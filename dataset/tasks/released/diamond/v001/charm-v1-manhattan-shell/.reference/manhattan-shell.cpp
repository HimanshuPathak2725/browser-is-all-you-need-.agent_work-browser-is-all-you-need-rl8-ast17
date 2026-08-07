#include <vector>
namespace charm::diamond {
struct Point {
    int x;
    int y;
    bool operator==(const Point& other) const { return x == other.x && y == other.y; }
};
inline std::vector<Point> shell(Point center, int radius) {
    if (radius < 0) return {};
    if (radius == 0) return {center};
    std::vector<Point> out;
    out.reserve(static_cast<std::size_t>(4 * radius));
    for (int step = 0; step < radius; ++step) out.push_back({center.x + step, center.y - radius + step});
    for (int step = 0; step < radius; ++step) out.push_back({center.x + radius - step, center.y + step});
    for (int step = 0; step < radius; ++step) out.push_back({center.x - step, center.y + radius - step});
    for (int step = 0; step < radius; ++step) out.push_back({center.x - radius + step, center.y - step});
    return out;
}
}
