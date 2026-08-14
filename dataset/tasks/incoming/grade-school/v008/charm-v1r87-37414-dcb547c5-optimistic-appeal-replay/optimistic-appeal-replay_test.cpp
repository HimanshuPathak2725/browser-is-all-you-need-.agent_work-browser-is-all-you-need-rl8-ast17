#include "optimistic-appeal-replay.cpp"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::grade_school;
int main() {
require_case(replay_grade_appeals({{"a",70}},{{"a",0,5},{"a",1,-2}}).value().at("a")==std::pair<int,std::size_t>{73,2});
require_case(replay_grade_appeals({},{}).value().empty());
require_case(!replay_grade_appeals({{"a",70}},{{"a",1,2}}));
require_case(!replay_grade_appeals({{"a",100}},{{"a",0,1}}));
require_case(!replay_grade_appeals({{"a",-1}},{}));
return 0;
}
