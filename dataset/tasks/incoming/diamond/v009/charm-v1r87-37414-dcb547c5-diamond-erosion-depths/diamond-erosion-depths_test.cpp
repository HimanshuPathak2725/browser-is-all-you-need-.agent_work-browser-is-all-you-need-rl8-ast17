#include "diamond-erosion-depths.hpp"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::diamond;
int main() {
CHECK(diamond_erosion_depths({"###","###","###"}).value()[1][1]==2);
CHECK(diamond_erosion_depths({".#"}).value()==std::vector<std::vector<int>>({{0,1}}));
CHECK(diamond_erosion_depths({"#"}).value()[0][0]==1);
CHECK(!diamond_erosion_depths({}));
CHECK(!diamond_erosion_depths({"##","#"}));
return 0;
}
