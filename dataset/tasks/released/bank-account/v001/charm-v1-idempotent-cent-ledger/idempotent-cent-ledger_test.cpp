#include "idempotent-cent-ledger.h"
#include <cassert>
#include <limits>
#include <string>
#include <vector>
using charm::bank::CentLedger;
int main() {
    CentLedger x;
    assert(!x.apply("", 4));
    assert(x.apply("seed", 100) && x.balance() == 100);
    assert(!x.apply("seed", 50) && x.balance() == 100);
    assert(x.apply("exact", -100) && x.balance() == 0);
    assert(!x.apply("over", -1) && x.accepted_ids().size() == 2);
    assert(x.apply("zero", 0));
    CentLedger y;
    assert(y.apply("max", std::numeric_limits<long long>::max()));
    assert(!y.apply("overflow", 1));
    assert((x.accepted_ids() == std::vector<std::string>{"seed", "exact", "zero"}));
    return 0;
}
