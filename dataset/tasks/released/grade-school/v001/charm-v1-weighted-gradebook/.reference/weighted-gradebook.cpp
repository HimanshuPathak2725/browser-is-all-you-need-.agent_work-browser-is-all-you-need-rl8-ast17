#include <algorithm>
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
