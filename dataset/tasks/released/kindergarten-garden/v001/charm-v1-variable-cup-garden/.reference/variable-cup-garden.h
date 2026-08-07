#pragma once
#include <optional>
#include <set>
#include <string>
#include <string_view>
#include <utility>
#include <vector>
namespace charm::garden {
class CupGarden {
public:
    static std::optional<CupGarden> parse(std::vector<std::string> rows, std::vector<std::string> students, std::size_t cups) {
        if (rows.empty() || students.empty() || cups == 0) return std::nullopt;
        const std::size_t width = students.size() * cups;
        for (const std::string& row : rows) if (row.size() != width) return std::nullopt;
        std::set<std::string> unique;
        for (const std::string& student : students) if (student.empty() || !unique.insert(student).second) return std::nullopt;
        return CupGarden(std::move(rows), std::move(students), cups);
    }
    std::vector<char> plants(std::string_view student) const {
        std::size_t index = students_.size();
        for (std::size_t i = 0; i < students_.size(); ++i) if (students_[i] == student) index = i;
        if (index == students_.size()) return {};
        std::vector<char> out;
        for (const std::string& row : rows_)
            for (std::size_t cup = 0; cup < cups_; ++cup) out.push_back(row[index * cups_ + cup]);
        return out;
    }
private:
    CupGarden(std::vector<std::string> rows, std::vector<std::string> students, std::size_t cups)
        : rows_(std::move(rows)), students_(std::move(students)), cups_(cups) {}
    std::vector<std::string> rows_;
    std::vector<std::string> students_;
    std::size_t cups_;
};
}
