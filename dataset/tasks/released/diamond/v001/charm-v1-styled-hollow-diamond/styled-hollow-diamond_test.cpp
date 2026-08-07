#include "styled-hollow-diamond.h"
#include <cassert>
#include <string>
#include <vector>
using charm::diamond::render_hollow;
int main() {
    assert(!render_hollow(0, '*', ' ') && !render_hollow(4, '*', ' '));
    assert((render_hollow(1, '#', ' ').value() == std::vector<std::string>{"#"}));
    assert((render_hollow(3, '*', ' ').value() == std::vector<std::string>{" *", "* *", " *"}));
    assert((render_hollow(3, '@', '.').value() == std::vector<std::string>{".@.", "@.@", ".@."}));
    assert(!render_hollow(3, '\n', '.'));
    const auto five = render_hollow(5, 'X', ' ');
    assert(five && five->size() == 5 && (*five)[2] == "X   X");
    for (const auto& line : *five) assert(line.empty() || line.back() != ' ');
    return 0;
}
