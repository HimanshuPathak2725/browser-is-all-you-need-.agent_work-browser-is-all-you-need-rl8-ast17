#pragma once
#include <string>
namespace charm::bank {
class CentLedger {
public:
    bool apply(std::string id, long long delta);
    long long balance() const;
    std::vector<std::string> accepted_ids() const;
};
}
