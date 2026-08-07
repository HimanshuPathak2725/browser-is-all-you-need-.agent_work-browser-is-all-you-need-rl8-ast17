#include "meal-mask-filter.hpp"

#include <cassert>

using namespace charm::v1n7::allergies;
int main() {
    assert((meals_avoiding_mask({{"soup",1U},{"rice",0U},{"pie",2U}},3U,1U).value()==std::vector<std::string>{"rice","pie"}));
    assert(meals_avoiding_mask({},0U,0U)->empty());
    assert(!meals_avoiding_mask({{"x",4U}},3U,0U));
    assert(!meals_avoiding_mask({{"x",0U},{"x",0U}},0U,0U));
    assert(!meals_avoiding_mask({},1U,2U));
    return 0;
}
