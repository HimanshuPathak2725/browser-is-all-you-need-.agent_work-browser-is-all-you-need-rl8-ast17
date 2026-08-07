#pragma once
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
