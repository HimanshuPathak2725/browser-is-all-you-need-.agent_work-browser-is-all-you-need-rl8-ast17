#include "diamond-erosion-depths.hpp"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::diamond;
int main() {
require_case(diamond_erosion_depths({"###","###","###"}).value()[1][1]==2);
require_case(diamond_erosion_depths({".#"}).value()==std::vector<std::vector<int>>({{0,1}}));
require_case(diamond_erosion_depths({"#"}).value()[0][0]==1);
require_case(!diamond_erosion_depths({}));
require_case(!diamond_erosion_depths({"##","#"}));
return 0;
}
