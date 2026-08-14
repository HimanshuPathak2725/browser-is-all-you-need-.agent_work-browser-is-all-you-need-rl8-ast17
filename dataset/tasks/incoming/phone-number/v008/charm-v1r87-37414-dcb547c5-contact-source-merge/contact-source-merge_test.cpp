#include "contact-source-merge.h"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::phone_number;
int main() {
require_case(merge_contact_sources({{"ann","111",2},{"ann","222",1}}).value().at("ann")=="222");
require_case(merge_contact_sources({{"ann","111",1},{"ann","111",1}}).value().at("ann")=="111");
require_case(merge_contact_sources({}).value().empty());
require_case(!merge_contact_sources({{"Ann","1",0}}));
require_case(!merge_contact_sources({{"a","1",0},{"a","2",0}}));
return 0;
}
