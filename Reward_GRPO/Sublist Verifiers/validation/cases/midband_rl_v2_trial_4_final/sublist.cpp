#include "sublist.h"

#include <algorithm>

namespace sublist {
namespace {

bool contains(const std::vector<int>& larger,
              const std::vector<int>& smaller) {
    if (smaller.empty()) {
        return true;
    }
    if (smaller.size() > larger.size()) {
        return false;
    }
    return std::search(
        larger.begin(), larger.end(),
        smaller.begin(), smaller.end()) != larger.end();
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
