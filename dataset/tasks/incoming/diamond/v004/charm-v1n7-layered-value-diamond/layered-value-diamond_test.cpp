#include "layered-value-diamond.cpp"

#include <cassert>

using charm::v1n7::diamond::render_layered_diamond;
int main(){assert(render_layered_diamond(0)->at(0)=="1");assert((render_layered_diamond(1).value()==std::vector<std::string>{".1.","121",".1."}));assert(render_layered_diamond(2)->at(2)=="12321");assert(!render_layered_diamond(-1));assert(!render_layered_diamond(15));return 0;}
