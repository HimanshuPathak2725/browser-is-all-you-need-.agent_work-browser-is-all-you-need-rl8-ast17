#include <limits>
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
        std::map<std::string, long long> totals;
        for (const auto& [name, dose] : batch) {
            if (name.empty() || dose < 0) {
                return {};
            }
            long long& total = totals[name];
            if (total > std::numeric_limits<long long>::max() - dose) {
                total = std::numeric_limits<long long>::max();
            } else {
                total += dose;
            }
        }
        std::vector<std::string> result;
        for (const auto& [name, limit] : limits_) {
            const auto found = totals.find(name);
            if (found != totals.end() && found->second > limit) {
                result.push_back(name);
            }
        }
        return result;
    }

private:
    std::map<std::string, int> limits_;
};

}  // namespace charm::allergy
