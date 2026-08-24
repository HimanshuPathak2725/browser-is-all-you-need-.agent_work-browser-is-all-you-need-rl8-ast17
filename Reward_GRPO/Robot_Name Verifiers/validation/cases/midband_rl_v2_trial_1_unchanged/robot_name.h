#pragma once

#include <string>

namespace robot_name {

class robot {
public:
    robot();
    std::string const& name() const;
    void reset();

private:
    std::string _name;
};

}  // namespace robot_name
