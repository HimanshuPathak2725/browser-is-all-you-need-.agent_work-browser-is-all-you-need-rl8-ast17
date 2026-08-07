#include "house-constraint-engine.h"
#include <cassert>
using charm::zebra::Clue;
using charm::zebra::ClueKind;
using charm::zebra::solve_unique;
int main() {
    assert(!solve_unique(0,{{"a"}},{}));
    assert(!solve_unique(2,{{"a"}},{}));
    assert(!solve_unique(2,{{"a","a"}},{}));
    const std::vector<std::vector<std::string>> categories{{"Ada","Bob"},{"cat","dog"}};
    assert(!solve_unique(2,categories,{}));
    const auto unique=solve_unique(2,categories,{{ClueKind::same_house,"Ada","dog"},{ClueKind::immediately_left,"Ada","Bob"}});
    assert(unique && unique->at("Ada")==0 && unique->at("dog")==0 && unique->at("Bob")==1);
    assert(!solve_unique(2,categories,{{ClueKind::same_house,"Ada","dog"},{ClueKind::same_house,"Ada","cat"}}));
    assert(!solve_unique(2,categories,{{ClueKind::same_house,"missing","cat"}}));
    const auto adjacent=solve_unique(2,categories,{{ClueKind::same_house,"Ada","cat"},{ClueKind::immediately_left,"cat","dog"}});
    assert(adjacent && adjacent->at("dog")==1);
    return 0;
}
