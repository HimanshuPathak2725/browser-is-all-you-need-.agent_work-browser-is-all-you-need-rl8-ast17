#pragma once

#include <string>
#include <vector>

namespace charm::allergy {

class ExposureWindowLedger {
public:
    void record(std::string name, int severity, int minute);
    std::vector<std::string> active(int minimum_severity,
                                    int now,
                                    int horizon) const;

private:
    struct Event {
        std::string name;
        int severity;
        int minute;
    };
    std::vector<Event> events_;
};

}  // namespace charm::allergy
