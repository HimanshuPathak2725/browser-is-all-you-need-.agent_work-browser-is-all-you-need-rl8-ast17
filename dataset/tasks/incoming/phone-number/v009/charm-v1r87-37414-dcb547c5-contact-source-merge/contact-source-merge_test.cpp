#include "contact-source-merge.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::phone_number;
int main() {
CHECK(merge_contact_sources({{"ann","111",2},{"ann","222",1}}).value().at("ann")=="222");
CHECK(merge_contact_sources({{"ann","111",1},{"ann","111",1}}).value().at("ann")=="111");
CHECK(merge_contact_sources({}).value().empty());
CHECK(!merge_contact_sources({{"Ann","1",0}}));
CHECK(!merge_contact_sources({{"a","1",0},{"a","2",0}}));
return 0;
}
