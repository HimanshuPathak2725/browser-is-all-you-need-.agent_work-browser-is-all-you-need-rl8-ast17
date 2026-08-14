#include "stable-bucket-relink.h"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::linked_list;
int main() {
require_case(stable_bucket_relink({1,0,1,0},2).value()==std::pair<int,std::vector<int>>{1,{2,3,-1,0}});
require_case(stable_bucket_relink({},0).value().first==-1);
require_case(stable_bucket_relink({0,0},1).value().second==std::vector<int>({1,-1}));
require_case(!stable_bucket_relink({0},0));
require_case(!stable_bucket_relink({2},2));
return 0;
}
