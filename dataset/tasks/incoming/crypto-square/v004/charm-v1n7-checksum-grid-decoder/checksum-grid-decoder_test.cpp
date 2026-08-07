#include "checksum-grid-decoder.hpp"

#include <cassert>

using charm::v1n7::crypto_square::decode_checked_grid;
int main(){assert(decode_checked_grid("abcda",2,2)=="acbd");assert(!decode_checked_grid("abcdb",2,2));assert(!decode_checked_grid("x0",0,1));assert(!decode_checked_grid("x0",1,0));assert(!decode_checked_grid("ab0",1,1));return 0;}
