"""Owner source for the three CHARM V1 Grade School tasks."""

from __future__ import annotations

from scripts.charm_v1_topics.common import package, prompt, support


ROSTER = r'''#pragma once
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
'''
ROSTER_START = ROSTER.replace("found->second = grade;", "students_.emplace(std::move(name), grade);")
ROSTER_TEST = r'''#include "moving-roster.h"
#include <cassert>
#include <string>
#include <utility>
#include <vector>
using charm::school::MovingRoster;
int main() {
    MovingRoster school;
    assert(!school.enroll("", 1) && !school.enroll("Ada", -1));
    assert(school.enroll("Zoe", 2) && school.enroll("Ada", 2) && school.enroll("Mia", 1));
    assert(!school.enroll("Ada", 3));
    assert((school.grade(2) == std::vector<std::string>{"Ada", "Zoe"}));
    assert(school.move("Zoe", 1));
    assert((school.grade(1) == std::vector<std::string>{"Mia", "Zoe"}));
    assert(!school.move("missing", 4) && !school.move("Ada", -1));
    assert((school.roster() == std::vector<std::pair<int,std::string>>{{1,"Mia"},{1,"Zoe"},{2,"Ada"}}));
    return 0;
}
'''


GRADEBOOK = r'''#include <algorithm>
#include <cmath>
#include <map>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>
namespace charm::school {
class WeightedGradebook {
public:
    bool set(std::string student, std::string assessment, int score, int weight) {
        if (student.empty() || assessment.empty() || score < 0 || score > 100 || weight <= 0) return false;
        data_[std::move(student)][std::move(assessment)] = {score, weight};
        return true;
    }
    std::optional<int> average_bp(std::string_view student) const {
        const auto found = data_.find(std::string(student));
        if (found == data_.end() || found->second.empty()) return std::nullopt;
        long long weighted = 0;
        long long total_weight = 0;
        for (const auto& [id, item] : found->second) { (void)id; weighted += static_cast<long long>(item.first) * item.second; total_weight += item.second; }
        return static_cast<int>(std::llround(static_cast<long double>(weighted) * 100.0L / total_weight));
    }
    std::vector<std::string> ranking() const {
        std::vector<std::pair<int,std::string>> values;
        for (const auto& [student, assessments] : data_) { (void)assessments; values.push_back({-*average_bp(student), student}); }
        std::sort(values.begin(), values.end());
        std::vector<std::string> out;
        for (const auto& item : values) out.push_back(item.second);
        return out;
    }
private:
    std::map<std::string,std::map<std::string,std::pair<int,int>>> data_;
};
}
'''
GRADEBOOK_TEST = r'''#include "weighted-gradebook.cpp"
#include <cassert>
#include <optional>
#include <string>
#include <vector>
using charm::school::WeightedGradebook;
int main() {
    WeightedGradebook book;
    assert(!book.set("", "quiz", 90, 1) && !book.set("Ada", "", 90, 1));
    assert(!book.set("Ada", "quiz", 101, 1) && !book.set("Ada", "quiz", 90, 0));
    assert(book.set("Ada", "quiz", 80, 1) && book.set("Ada", "exam", 100, 3));
    assert(book.average_bp("Ada") == std::optional<int>(9500));
    assert(book.set("Ada", "quiz", 100, 1) && book.average_bp("Ada") == std::optional<int>(10000));
    assert(!book.average_bp("unknown"));
    assert(book.set("Bob", "one", 100, 1) && book.set("Amy", "one", 100, 1));
    assert((book.ranking() == std::vector<std::string>{"Ada", "Amy", "Bob"}));
    return 0;
}
'''


ATTENDANCE = r'''#pragma once
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
'''
ATTENDANCE_START = r'''#pragma once
#include <string>
#include <utility>
#include <vector>
namespace charm::school {
class AttendanceBook {
public:
    bool add_student(std::string);
    bool record_day(const std::vector<std::pair<std::string,bool>>&);
    std::pair<int,int> totals(std::string_view) const;
};
}
'''
ATTENDANCE_TEST = r'''#include "attendance-transaction-repair.h"
#include <cassert>
using charm::school::AttendanceBook;
int main() {
    AttendanceBook book;
    assert(!book.add_student("") && book.add_student("Ada") && book.add_student("Bob"));
    assert(!book.add_student("Ada"));
    assert(book.record_day({{"Ada",true},{"Bob",false}}));
    assert(book.totals("Ada") == std::make_pair(1,1));
    assert(book.totals("Bob") == std::make_pair(0,1));
    assert(!book.record_day({{"Ada",true},{"Ada",false}}));
    assert(book.totals("Ada") == std::make_pair(1,1));
    assert(!book.record_day({{"Ada",true},{"Eve",true}}));
    assert(!book.record_day({{"Ada",true}}));
    assert(book.totals("missing") == std::make_pair(-1,-1));
    return 0;
}
'''


def tasks() -> list[dict]:
    roster = ["moving-roster.h", "moving-roster.cpp"]
    gradebook = ["weighted-gradebook.cpp"]
    attendance = ["attendance-transaction-repair.h", "attendance-transaction-repair.cpp"]
    return [
        package(topic="Grade School", task_id="charm-v1-moving-roster", instructions=prompt("Moving roster", "Maintain exactly one nonnegative grade per unique student, move enrolled students atomically, and return deterministic grade and school listings.", "namespace charm::school { class MovingRoster { public: bool enroll(std::string,int); bool move(std::string,int); std::vector<std::string> grade(int) const; std::vector<std::pair<int,std::string>> roster() const; }; }", ["empty names and negative grades reject", "duplicate enrollment rejects", "move requires an existing student", "grade names are lexical", "roster sorts by grade then name"], roster), editable={roster[0]: ROSTER_START, roster[1]: support(roster[0], 81)}, reference={roster[0]: ROSTER, roster[1]: support(roster[0], 82)}, hidden_name="moving-roster_test.cpp", hidden=ROSTER_TEST, category="mutable-roster", tags=["header-reconstruction", "move", "ordering", "state"]),
        package(topic="Grade School", task_id="charm-v1-weighted-gradebook", instructions=prompt("Weighted gradebook", "Store replaceable assessments and rank students by rounded weighted average in basis points, breaking ties lexically.", "namespace charm::school { class WeightedGradebook { public: bool set(std::string,std::string,int,int); std::optional<int> average_bp(std::string_view) const; std::vector<std::string> ranking() const; }; }", ["scores are 0..100", "weights are positive", "assessment IDs replace per student", "averages round to nearest basis point", "ranking ties are lexical"], gradebook), editable={gradebook[0]: "#include <string>\nnamespace charm::school { class WeightedGradebook {}; }\n"}, reference={gradebook[0]: GRADEBOOK}, hidden_name="weighted-gradebook_test.cpp", hidden=GRADEBOOK_TEST, category="weighted-ranking", tags=["cpp-only", "rounding", "replacement", "ranking"]),
        package(topic="Grade School", task_id="charm-v1-attendance-transaction-repair", instructions=prompt("Attendance transaction repair", "Record complete daily attendance batches atomically. Every known student appears exactly once or no totals change.", "namespace charm::school { class AttendanceBook { public: bool add_student(std::string); bool record_day(const std::vector<std::pair<std::string,bool>>&); std::pair<int,int> totals(std::string_view) const; }; }", ["duplicate students reject", "unknown students reject", "missing students reject", "invalid batches leave all totals unchanged", "unknown total query returns {-1,-1}"], attendance), editable={attendance[0]: ATTENDANCE_START, attendance[1]: support(attendance[0], 83)}, reference={attendance[0]: ATTENDANCE, attendance[1]: support(attendance[0], 84)}, hidden_name="attendance-transaction-repair_test.cpp", hidden=ATTENDANCE_TEST, category="attendance-transaction", tags=["compile-repair", "atomic-batch", "header-extension", "duplicates"]),
    ]
