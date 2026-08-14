#include "optimistic-appeal-replay.cpp"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::grade_school;
int main() {
CHECK(replay_grade_appeals({{"a",70}},{{"a",0,5},{"a",1,-2}}).value().at("a")==std::pair<int,std::size_t>{73,2});
CHECK(replay_grade_appeals({},{}).value().empty());
CHECK(!replay_grade_appeals({{"a",70}},{{"a",1,2}}));
CHECK(!replay_grade_appeals({{"a",100}},{{"a",0,1}}));
CHECK(!replay_grade_appeals({{"a",-1}},{}));
return 0;
}
