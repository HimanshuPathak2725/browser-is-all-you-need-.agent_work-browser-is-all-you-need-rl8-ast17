#include "rectangular-outline-diamond.h"

#include <cassert>

using charm::v1n7::diamond::render_outline_diamond;
int main(){assert((render_outline_diamond(1,'#','.').value()==std::vector<std::string>{".#.","#.#",".#."}));assert(render_outline_diamond(0,'x',' ')->at(0)=="x");assert(!render_outline_diamond(-1,'x',' '));assert(!render_outline_diamond(1,'x','x'));assert(render_outline_diamond(2,'*','-')->size()==5);return 0;}
