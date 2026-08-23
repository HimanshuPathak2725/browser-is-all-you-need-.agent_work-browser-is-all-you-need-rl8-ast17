#include "robot_name.h"

#include <algorithm>
#include <array>
#include <random>
#include <string>
#include <utility>
#include <unordered_set>
#include <vector>

namespace robot_name {

robot::robot() {
    reset();
}

std::string const& robot::name() const {
    return _name;
}

void robot::reset() {
    static std::unordered_set<std::string> used_names;
    static thread_local std::mt19937 engine{std::random_device{}()};
    static std::uniform_int_distribution<int> letters{'A', 'Z'};
    static std::uniform_int_distribution<int> digits{'0', '9'};

    std::string name;
    do {
        std::array<char, 5> characters{};
        std::generate(characters.begin(), characters.end(), []() {
            if (std::rand() % 2 == 0) {
                return static_cast<char>(letters(engine));
            } else {
                return static_cast<char>(digits(engine));
            }
        });
        name = std::string(characters.begin(), characters.end());
    } while (used_names.find(name) != used_names.end());

    used_names.insert(name);
    _name = name;
}

}  // namespace robot_name
