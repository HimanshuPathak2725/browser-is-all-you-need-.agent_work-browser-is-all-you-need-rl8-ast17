#include <map>
#include <string>
#include <utility>
#include <vector>

namespace charm::allergy {

class DosePolicyTable {
public:
    bool set_limit(std::string name, int limit) {
        if (name.empty() || limit < 0) {
            return false;
        }
        limits_[std::move(name)] = limit;
        return true;
    }

    std::vector<std::string> exceeded(
        const std::vector<std::pair<std::string, int>>& batch) const {
        (void)batch;
        return {};
    }

private:
    std::map<std::string, int> limits_;
};

}  // namespace charm::allergy
