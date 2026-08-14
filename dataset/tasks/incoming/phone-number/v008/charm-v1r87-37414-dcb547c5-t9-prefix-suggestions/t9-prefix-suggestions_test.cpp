#include "t9-prefix-suggestions.h"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::phone_number;
int main() {
require_case(t9_prefix_suggestions({"tree","used","apple"},"873",9).value()==std::vector<std::string>({"tree","used"}));
require_case(t9_prefix_suggestions({"a"},"2",0).value().empty());
require_case(t9_prefix_suggestions({},"2",4).value().empty());
require_case(!t9_prefix_suggestions({"A"},"2",1));
require_case(!t9_prefix_suggestions({"a"},"1",1));
return 0;
}
