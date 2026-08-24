#include "robot_name.h"
#include <atomic>
#include <set>

namespace robot_name {

std::mt19937 robot::engine_(std::random_device{}());
std::uniform_int_distribution<char> robot::letters_('A', 'Z');
std::uniform_int_distribution<char> robot::digits_('0', '9');

robot::robot() {
    reset();
}

std::string const& robot::name() const {
    return name_;
}

void robot::reset() {
    std::string candidate;
    candidate += letters_(engine_);
    candidate += letters_(engine_);
    candidate += digits_(engine_);
    candidate += digits_(engine_);
    candidate += digits_(engine_);

    static std::set<std::string> used_names;
    while (used_names.find(candidate) != used_names.end()) {
        candidate += letters_(engine_);
        candidate += letters_(engine_);
        candidate += digits_(engine_);
        candidate += digits_(engine_);
        candidate += digits_(engine_);
    }
    used_names.insert(candidate);
    name_ = candidate;
}

}  // namespace robot_name
