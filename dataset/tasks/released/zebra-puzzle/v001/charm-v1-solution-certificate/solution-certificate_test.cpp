#include "solution-certificate.cpp"
#include <cassert>
using charm::zebra::ClueKind;
using charm::zebra::verify;
int main() {
    const std::vector<std::vector<std::string>> categories{{"Ada","Bob"},{"cat","dog"}};
    const std::vector<charm::zebra::Clue> clues{{ClueKind::same_house,"Ada","cat"},{ClueKind::immediately_left,"Ada","Bob"},{ClueKind::adjacent,"cat","dog"}};
    const auto good=verify(2,categories,clues,{{"Ada",0},{"Bob",1},{"cat",0},{"dog",1}});
    assert(good.complete && good.violated.empty());
    const auto wrong=verify(2,categories,clues,{{"Ada",1},{"Bob",0},{"cat",0},{"dog",1}});
    assert(wrong.complete && wrong.violated==std::vector<std::size_t>({0,1}));
    const auto missing=verify(2,categories,clues,{{"Ada",0},{"Bob",1},{"cat",0}});
    assert(!missing.complete && missing.violated==std::vector<std::size_t>({2}));
    const auto duplicate=verify(2,categories,clues,{{"Ada",0},{"Bob",0},{"cat",0},{"dog",1}});
    assert(!duplicate.complete);
    const auto extra=verify(2,categories,clues,{{"Ada",0},{"Bob",1},{"cat",0},{"dog",1},{"fox",0}});
    assert(!extra.complete);
    assert(!verify(0,categories,clues,{}).complete);
    return 0;
}
