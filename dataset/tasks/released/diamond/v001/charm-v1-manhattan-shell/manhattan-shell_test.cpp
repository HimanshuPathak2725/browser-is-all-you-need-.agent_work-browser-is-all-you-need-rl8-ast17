#include "manhattan-shell.cpp"
#include <cassert>
#include <set>
#include <utility>
#include <vector>
#include <cstdlib>
using charm::diamond::Point;
using charm::diamond::shell;
int main() {
    assert(shell({2, 3}, -1).empty());
    const auto radius_zero = shell({2, 3}, 0);
    const std::vector<Point> expected_zero{{2, 3}};
    assert(radius_zero == expected_zero);
    const auto radius_one = shell({0, 0}, 1);
    const std::vector<Point> expected_one{{0,-1},{1,0},{0,1},{-1,0}};
    assert(radius_one == expected_one);
    const auto radius_two = shell({1, -1}, 2);
    assert((radius_two.size() == 8 && radius_two.front() == Point{1, -3}));
    assert((radius_two[2] == Point{3, -1} && radius_two[4] == Point{1, 1}));
    std::set<std::pair<int,int>> unique;
    for (Point point : radius_two) unique.insert({point.x, point.y});
    assert(unique.size() == radius_two.size());
    for (Point point : radius_two) assert(std::abs(point.x - 1) + std::abs(point.y + 1) == 2);
    return 0;
}
