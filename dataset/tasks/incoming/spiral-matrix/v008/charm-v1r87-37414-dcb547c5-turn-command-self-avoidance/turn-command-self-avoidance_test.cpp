#include "turn-command-self-avoidance.cpp"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::spiral_matrix;
int main() {
require_case(replay_self_avoiding_turns("FFRFF").value().back()==GridPoint{-2,2});
require_case(replay_self_avoiding_turns("").value()==std::vector<GridPoint>{{0,0}});
require_case(replay_self_avoiding_turns("LLLL").value().size()==1);
require_case(!replay_self_avoiding_turns("FRFRFRF"));
require_case(!replay_self_avoiding_turns("X"));
return 0;
}
