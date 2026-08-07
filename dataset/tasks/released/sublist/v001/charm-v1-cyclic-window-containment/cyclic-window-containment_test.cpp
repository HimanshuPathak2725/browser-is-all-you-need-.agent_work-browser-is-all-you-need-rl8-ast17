#include "cyclic-window-containment.cpp"
#include <cassert>
#include <optional>
using charm::sublist::cyclic_find;
int main() {
    assert(cyclic_find({}, {}) == std::optional<std::size_t>(0));
    assert(cyclic_find({1,2,3}, {}) == std::optional<std::size_t>(0));
    assert(!cyclic_find({}, {1}));
    assert(!cyclic_find({1,2}, {1,2,1}));
    assert(cyclic_find({1,2,3,4}, {3,4,1}) == std::optional<std::size_t>(2));
    assert(cyclic_find({1,2,1,2}, {1,2}) == std::optional<std::size_t>(0));
    assert(!cyclic_find({1,2,3}, {2,1}));
    assert(cyclic_find({7}, {7}) == std::optional<std::size_t>(0));
    return 0;
}
