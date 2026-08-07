#include "weekly-window-intersection.cpp"
#include <cassert>
#include <vector>
using charm::clockwork::Window;
using charm::clockwork::intersect_weekly;
static bool same(const std::vector<Window>& a, const std::vector<Window>& b) {
    if (a.size() != b.size()) return false;
    for (std::size_t i = 0; i < a.size(); ++i) if (a[i].begin != b[i].begin || a[i].end != b[i].end) return false;
    return true;
}
int main() {
    assert(same(intersect_weekly({10, 20}, {15, 30}), {{15, 20}}));
    assert(intersect_weekly({10, 20}, {20, 30}).empty());
    assert(same(intersect_weekly({10000, 20}, {10, 15}), {{10, 15}}));
    assert(same(intersect_weekly({10000, 20}, {9990, 10}), {{0, 10}, {10000, 10080}}));
    assert(intersect_weekly({4, 4}, {0, 9}).empty());
    assert(intersect_weekly({-1, 4}, {0, 9}).empty());
    assert(same(intersect_weekly({0, 100}, {25, 75}), {{25, 75}}));
    return 0;
}
