#include "avl-certificate-audit.cpp"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::binary_search_tree;
int main() {
require_case(audit_avl_certificate({{2,1,2},{1,-1,-1},{3,-1,-1}},0)==2);
require_case(audit_avl_certificate({},-1)==0);
require_case(!audit_avl_certificate({{2,1,-1},{1,2,-1},{0,-1,-1}},0));
require_case(!audit_avl_certificate({{2,1,1},{1,-1,-1}},0));
require_case(!audit_avl_certificate({{2,-1,-1},{1,-1,-1}},0));
return 0;
}
