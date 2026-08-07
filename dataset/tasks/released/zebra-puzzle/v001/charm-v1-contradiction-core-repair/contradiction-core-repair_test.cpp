#include "contradiction-core-repair.h"
#include <cassert>
using charm::zebra::Clue;
using charm::zebra::ClueKind;
using charm::zebra::contradiction_core;
int main(){
    const std::vector<std::vector<std::string>> categories{{"Ada","Bob"},{"cat","dog"}};
    assert(contradiction_core(2,categories,{}).empty());
    const std::vector<Clue> satisfiable{{ClueKind::same_house,"Ada","cat"}};
    assert(contradiction_core(2,categories,satisfiable).empty());
    const std::vector<Clue> contradictory{{ClueKind::same_house,"Ada","cat"},{ClueKind::same_house,"Ada","dog"},{ClueKind::adjacent,"cat","dog"}};
    const auto core=contradiction_core(2,categories,contradictory);
    assert(core==std::vector<std::size_t>({0,1}));
    const std::vector<Clue> order{{ClueKind::immediately_left,"Ada","Bob"},{ClueKind::immediately_left,"Bob","Ada"}};
    assert(contradiction_core(2,categories,order)==std::vector<std::size_t>({0,1}));
    const auto repeated=contradiction_core(2,categories,contradictory);assert(repeated==core);
    assert(!core.empty());
    return 0;
}
