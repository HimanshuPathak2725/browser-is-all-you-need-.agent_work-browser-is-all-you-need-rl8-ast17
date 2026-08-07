#pragma once
#include <algorithm>
#include <map>
#include <string>
#include <string_view>
#include <utility>
#include <vector>
namespace charm::school {
class MovingRoster {
public:
    bool enroll(std::string name, int grade) {
        if (name.empty() || grade < 0 || students_.count(name) != 0U) return false;
        students_.emplace(std::move(name), grade);
        return true;
    }
    bool move(std::string name, int grade) {
        if (grade < 0) return false;
        auto found = students_.find(name);
        if (found == students_.end()) return false;
        found->second = grade;
        return true;
    }
    std::vector<std::string> grade(int grade_number) const {
        std::vector<std::string> out;
        for (const auto& [name, current] : students_) if (current == grade_number) out.push_back(name);
        return out;
    }
    std::vector<std::pair<int,std::string>> roster() const {
        std::vector<std::pair<int,std::string>> out;
        for (const auto& [name, current] : students_) out.push_back({current, name});
        std::sort(out.begin(), out.end());
        return out;
    }
private:
    std::map<std::string,int> students_;
};
}
