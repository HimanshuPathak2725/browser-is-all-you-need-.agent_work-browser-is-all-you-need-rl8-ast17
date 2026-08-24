#include "robot_name.h"

#include <random>
#include <string>
#include <unordered_set>

namespace robot_name {

robot::robot() = default;

std::string const& robot::name() const {
    if (_name.empty()) {
        _name = generate_name();
    }
    return _name;
}

void robot::reset() {
    _name.clear();
}

std::string robot::generate_name() {
    static std::mt19937 engine{std::random_device{}()};
    static std::uniform_int_distribution<int> letters('A', 'Z');
    static std::uniform_int_distribution<int> digits('0', '9');

    std::string result;
    result.push_back(static_cast<char>(letters(engine)));
    result.push_back(static_cast<char>(letters(engine)));
    result.push_back(static_cast<char>(digits(engine)));
    result.push_back(static_cast<char>(digits(engine)));
    result.push_back(static_cast<char>(digits(engine)));

    static std::unordered_set<std::string> assigned_names;
    const auto found = assigned_names.find(result);
    if (found != assigned_names.end()) {
        return generate_name();
    }
    assigned_names.insert(result);
    return result;
}

}  // namespace robot_name
