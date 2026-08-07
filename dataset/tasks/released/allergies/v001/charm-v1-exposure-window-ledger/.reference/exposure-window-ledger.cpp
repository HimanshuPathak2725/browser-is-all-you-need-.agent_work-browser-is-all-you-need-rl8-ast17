#include "exposure-window-ledger.h"

#include <set>
#include <utility>

namespace charm::allergy::detail {
bool within_inclusive_window(int minute, int now, int horizon);
}

namespace charm::allergy {

void ExposureWindowLedger::record(std::string name, int severity, int minute) {
    if (name.empty() || severity < 0) {
        return;
    }
    events_.push_back(Event{std::move(name), severity, minute});
}

std::vector<std::string> ExposureWindowLedger::active(
    int minimum_severity, int now, int horizon) const {
    if (horizon < 0) {
        return {};
    }
    std::set<std::string> names;
    for (const Event& event : events_) {
        if (event.severity >= minimum_severity &&
            detail::within_inclusive_window(event.minute, now, horizon)) {
            names.insert(event.name);
        }
    }
    return {names.begin(), names.end()};
}

}  // namespace charm::allergy
