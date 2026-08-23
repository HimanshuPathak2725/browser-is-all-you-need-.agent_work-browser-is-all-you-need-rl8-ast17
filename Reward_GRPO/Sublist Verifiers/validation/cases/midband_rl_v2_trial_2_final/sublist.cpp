#include "sublist.h"

#include <algorithm>

namespace sublist {
namespace {

bool contains(const std::vector<int>& candidate,
              const std::vector<int>& source) {
    if (candidate.empty()) {
        return true;
    }
    if (candidate.size() > source.size()) {
        return false;
    }
    return std::search(
        source.begin(), source.end(),
        candidate.begin(), candidate.end()) != source.end();
}

}  // namespace

List_comparison sublist(const std::vector<int>& list_one,
                        const std::vector<int>& list_two) {
    if (list_one == list_two) {
        return List_comparison::equal;
    }
    if (contains(list_one, list_two)) {
        return List_comparison::sublist;
    }
    if (contains(list_two, list_one)) {
        return List_comparison::superlist;
    }
    return List_comparison::unequal;
}

}  // namespace sublist
