#include "t9-prefix-suggestions.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::phone_number;
int main() {
CHECK(t9_prefix_suggestions({"tree","used","apple"},"873",9).value()==std::vector<std::string>({"tree","used"}));
CHECK(t9_prefix_suggestions({"a"},"2",0).value().empty());
CHECK(t9_prefix_suggestions({},"2",4).value().empty());
CHECK(!t9_prefix_suggestions({"A"},"2",1));
CHECK(!t9_prefix_suggestions({"a"},"1",1));
return 0;
}
