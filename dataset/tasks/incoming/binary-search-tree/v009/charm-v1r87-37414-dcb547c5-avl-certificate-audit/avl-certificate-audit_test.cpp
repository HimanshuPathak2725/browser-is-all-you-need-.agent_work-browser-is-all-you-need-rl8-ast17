#include "avl-certificate-audit.cpp"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::binary_search_tree;
int main() {
CHECK(audit_avl_certificate({{2,1,2},{1,-1,-1},{3,-1,-1}},0)==2);
CHECK(audit_avl_certificate({},-1)==0);
CHECK(!audit_avl_certificate({{2,1,-1},{1,2,-1},{0,-1,-1}},0));
CHECK(!audit_avl_certificate({{2,1,1},{1,-1,-1}},0));
CHECK(!audit_avl_certificate({{2,-1,-1},{1,-1,-1}},0));
return 0;
}
