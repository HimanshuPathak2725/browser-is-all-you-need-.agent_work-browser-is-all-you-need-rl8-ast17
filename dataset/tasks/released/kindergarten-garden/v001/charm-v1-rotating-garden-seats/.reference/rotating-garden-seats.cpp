#include <string>
#include <string_view>
#include <utility>
#include <vector>
namespace charm::garden {
class RotatingGarden {
public:
    RotatingGarden(std::vector<std::string> students, std::vector<char> plants)
        : students_(std::move(students)), plants_(std::move(plants)) {}
    std::vector<char> plants_for(std::string_view student, long long day) const {
        if (students_.empty() || plants_.size() % students_.size() != 0) return {};
        std::size_t student_index = students_.size();
        for (std::size_t i = 0; i < students_.size(); ++i) if (students_[i] == student) student_index = i;
        if (student_index == students_.size()) return {};
        const long long count = static_cast<long long>(students_.size());
        long long shift = day % count;
        if (shift < 0) shift += count;
        const std::size_t seat = (student_index + static_cast<std::size_t>(shift)) % students_.size();
        const std::size_t cups = plants_.size() / students_.size();
        return {plants_.begin() + static_cast<long long>(seat * cups), plants_.begin() + static_cast<long long>((seat + 1) * cups)};
    }
private:
    std::vector<std::string> students_;
    std::vector<char> plants_;
};
}
