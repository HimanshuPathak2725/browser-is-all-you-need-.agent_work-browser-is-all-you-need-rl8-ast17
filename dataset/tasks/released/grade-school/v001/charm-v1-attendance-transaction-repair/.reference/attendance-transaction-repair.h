#pragma once
#include <map>
#include <set>
#include <string>
#include <string_view>
#include <utility>
#include <vector>
namespace charm::school {
class AttendanceBook {
public:
    bool add_student(std::string name) {
        if (name.empty()) return false;
        return totals_.emplace(std::move(name), std::pair<int,int>{0,0}).second;
    }
    bool record_day(const std::vector<std::pair<std::string,bool>>& entries) {
        if (entries.size() != totals_.size()) return false;
        std::set<std::string> seen;
        for (const auto& entry : entries)
            if (totals_.count(entry.first) == 0U || !seen.insert(entry.first).second) return false;
        for (const auto& entry : entries) { auto& total = totals_[entry.first]; ++total.second; if (entry.second) ++total.first; }
        return true;
    }
    std::pair<int,int> totals(std::string_view name) const {
        const auto found = totals_.find(std::string(name));
        return found == totals_.end() ? std::pair<int,int>{-1,-1} : found->second;
    }
private:
    std::map<std::string,std::pair<int,int>> totals_;
};
}
