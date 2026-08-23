#pragma once

#include <string>
#include <random>

namespace robot_name {

class robot {
public:
    robot();
    std::string const& name() const;
    void reset();

private:
    std::string name_;
    static std::mt19937 engine_;
    static std::uniform_int_distribution<char> letters_;
    static std::uniform_int_distribution<char> digits_;
};

}  // namespace robot_name
