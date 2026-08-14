#include "stable-bucket-relink.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::linked_list;
int main() {
CHECK(stable_bucket_relink({1,0,1,0},2).value()==std::pair<int,std::vector<int>>{1,{2,3,-1,0}});
CHECK(stable_bucket_relink({},0).value().first==-1);
CHECK(stable_bucket_relink({0,0},1).value().second==std::vector<int>({1,-1}));
CHECK(!stable_bucket_relink({0},0));
CHECK(!stable_bucket_relink({2},2));
return 0;
}
