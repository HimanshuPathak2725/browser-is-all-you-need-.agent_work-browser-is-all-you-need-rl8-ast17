#include "corner-directed-spiral-path.h"

#include <cassert>

using namespace charm::v1n7::spiral_matrix;
int main(){assert((clockwise_spiral_path(2,3,Corner::top_left).value()==std::vector<std::pair<std::size_t,std::size_t>>{{0,0},{0,1},{0,2},{1,2},{1,1},{1,0}}));assert(clockwise_spiral_path(0,3,Corner::top_left)->empty());assert((clockwise_spiral_path(1,1,Corner::bottom_right)->at(0)==std::pair<std::size_t,std::size_t>(0,0)));assert((clockwise_spiral_path(2,2,Corner::top_right)->front()==std::pair<std::size_t,std::size_t>(0,1)));assert(clockwise_spiral_path(2,1,Corner::bottom_left)->size()==2);return 0;}
