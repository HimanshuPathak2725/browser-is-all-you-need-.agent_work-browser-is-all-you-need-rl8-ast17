#include "exposure-window-ledger.h"

#include <cassert>
#include <limits>
#include <string>
#include <vector>

using charm::allergy::ExposureWindowLedger;

int main() {
    ExposureWindowLedger empty;
    assert(empty.active(0, 10, 5).empty());

    ExposureWindowLedger ledger;
    ledger.record("pollen", 4, 90);
    ledger.record("dust", 7, 95);
    ledger.record("pollen", 9, 100);
    ledger.record("mold", 10, 101);
    assert((ledger.active(7, 100, 5) == std::vector<std::string>{"dust", "pollen"}));

    assert((ledger.active(4, 100, 10) == std::vector<std::string>{"dust", "pollen"}));

    ledger.record("", 100, 100);
    ledger.record("latex", -1, 100);
    assert((ledger.active(0, 100, 0) == std::vector<std::string>{"pollen"}));

    ledger.record("cedar", 8, std::numeric_limits<int>::min());
    assert((ledger.active(8, std::numeric_limits<int>::min(), 0) ==
            std::vector<std::string>{"cedar"}));

    assert(ledger.active(0, 100, -1).empty());
    return 0;
}
