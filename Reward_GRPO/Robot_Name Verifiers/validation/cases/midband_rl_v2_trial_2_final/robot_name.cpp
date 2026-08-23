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
    static thread_local std::unordered_set<std::string> used_names;
    static thread_local std::mt19937 engine{std::random_device{}()};
    static thread_local std::uniform_int_distribution<int> letters{'A', 'Z'};
    static thread_local std::uniform_int_distribution<int> digits{'0', '9'};

    std::string name;
    do {
        std::array<char, 5> characters{};
        characters[0] = static_cast<char>(letters(engine));
        characters[1] = static_cast<char>(letters(engine));
        characters[2] = static_cast<char>(digits(engine));
        characters[3] = static_cast<char>(digits(engine));
        characters[4] = static_cast<char>(digits(engine));
        name = std::string(characters.begin(), characters.end());
    } while (used_names.find(name) != used_names.end());

    used_names.insert(name);
    _name = name;
}

}  // namespace robot_name
