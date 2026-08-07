#include "complete-spiral-path-validator.h"

#include <cassert>

using charm::v1n7::spiral_matrix::validates_clockwise_spiral;
int main(){assert(validates_clockwise_spiral(2,2,{{0,0},{0,1},{1,1},{1,0}}));assert(validates_clockwise_spiral(0,5,{}));assert(!validates_clockwise_spiral(1,2,{{0,0}}));assert(!validates_clockwise_spiral(2,2,{{0,0},{1,0},{1,1},{0,1}}));assert(!validates_clockwise_spiral(1,1,{{1,0}}));return 0;}
