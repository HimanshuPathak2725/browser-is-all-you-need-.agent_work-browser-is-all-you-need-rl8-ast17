#include <map>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
namespace charm::phone {
class DialPlan {
public:
    bool add(std::string prefix, std::string route_name) {
        if (prefix.empty() || route_name.empty()) return false;
        for (unsigned char ch : prefix) if (ch < '0' || ch > '9') return false;
        return routes_.emplace(std::move(prefix), std::move(route_name)).second;
    }
    std::optional<std::pair<std::string,std::string>> route(std::string_view digits) const {
        for (unsigned char ch : digits) if (ch < '0' || ch > '9') return std::nullopt;
        const std::pair<const std::string,std::string>* best = nullptr;
        for (const auto& item : routes_) if (digits.substr(0, item.first.size()) == item.first && (!best || item.first.size() > best->first.size())) best = &item;
        if (!best) return std::nullopt;
        return std::pair<std::string,std::string>{best->second, std::string(digits.substr(best->first.size()))};
    }
private:
    std::map<std::string,std::string> routes_;
};
}
