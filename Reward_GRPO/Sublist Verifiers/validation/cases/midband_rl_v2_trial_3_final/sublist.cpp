#include "sublist.h"

#include <algorithm>

namespace sublist {

namespace {

bool contains(const std::vector<int>& bigger,
              const std::vector<int>& smaller) {
    if (smaller.empty()) {
        return true;
    }
    if (bigger.size() < smaller.size()) {
        return false;
    }
    for (size_t begin = 0; begin <= bigger.size() - smaller.size(); ++begin) {
        if (std::equal(smaller.begin(), smaller.end(),
                        bigger.begin() + begin)) {
            return true;
        }
    }
    return false;
}

}  // namespace

List_comparison sublist(const std::vector<int>& list_one,
                        const std::vector<int>& list_two) {
    if (list_one == list_two) {
        return List_comparison::equal;
    }
    if (contains(list_two, list_one)) {
        return List_comparison::sublist;
    }
    if (contains(list_one, list_two)) {
        return List_comparison::superlist;
    }
    return List_comparison::unequal;
}

}  // namespace sublist
