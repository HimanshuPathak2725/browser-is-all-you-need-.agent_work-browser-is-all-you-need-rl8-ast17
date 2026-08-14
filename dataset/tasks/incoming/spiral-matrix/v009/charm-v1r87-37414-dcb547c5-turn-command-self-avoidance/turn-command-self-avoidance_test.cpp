#include "turn-command-self-avoidance.cpp"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::spiral_matrix;
int main() {
CHECK(replay_self_avoiding_turns("FFRFF").value().back()==GridPoint{-2,2});
CHECK(replay_self_avoiding_turns("").value()==std::vector<GridPoint>{{0,0}});
CHECK(replay_self_avoiding_turns("LLLL").value().size()==1);
CHECK(!replay_self_avoiding_turns("FRFRFRF"));
CHECK(!replay_self_avoiding_turns("X"));
return 0;
}
