#include "dose-policy-table.cpp"

#include <cassert>
#include <string>
#include <utility>
#include <vector>

using charm::allergy::DosePolicyTable;

int main() {
    DosePolicyTable table;
    assert(!table.set_limit("", 2) && !table.set_limit("dust", -1));
    assert(table.set_limit("dust", 5) && table.set_limit("pollen", 3));

    assert((table.exceeded({{"dust", 2}, {"dust", 4}}) ==
            std::vector<std::string>{"dust"}));

    assert((table.exceeded({{"unknown", 100}, {"pollen", 3}}).empty()));

    assert(table.exceeded({{"dust", 9}, {"", 1}}).empty());

    assert(table.set_limit("pollen", 0));
    assert((table.exceeded({{"pollen", 1}, {"dust", 6}}) ==
            std::vector<std::string>{"dust", "pollen"}));

    assert(table.exceeded({{"dust", -1}}).empty());
    return 0;
}
