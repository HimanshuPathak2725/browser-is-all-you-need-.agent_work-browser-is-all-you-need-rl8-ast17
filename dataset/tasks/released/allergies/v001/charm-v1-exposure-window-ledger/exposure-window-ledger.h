#pragma once

#include <string>
#include <vector>

namespace charm::allergy {

class ExposureWindowLedger {
public:
    void record(std::string name, int severity);
    std::vector<std::string> active(int minimum_severity, int now) const;
};

}  // namespace charm::allergy
