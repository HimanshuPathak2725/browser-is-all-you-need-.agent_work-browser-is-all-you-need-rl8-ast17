#include "moving-roster.h"
#include <cassert>
#include <string>
#include <utility>
#include <vector>
using charm::school::MovingRoster;
int main() {
    MovingRoster school;
    assert(!school.enroll("", 1) && !school.enroll("Ada", -1));
    assert(school.enroll("Zoe", 2) && school.enroll("Ada", 2) && school.enroll("Mia", 1));
    assert(!school.enroll("Ada", 3));
    assert((school.grade(2) == std::vector<std::string>{"Ada", "Zoe"}));
    assert(school.move("Zoe", 1));
    assert((school.grade(1) == std::vector<std::string>{"Mia", "Zoe"}));
    assert(!school.move("missing", 4) && !school.move("Ada", -1));
    assert((school.roster() == std::vector<std::pair<int,std::string>>{{1,"Mia"},{1,"Zoe"},{2,"Ada"}}));
    return 0;
}
