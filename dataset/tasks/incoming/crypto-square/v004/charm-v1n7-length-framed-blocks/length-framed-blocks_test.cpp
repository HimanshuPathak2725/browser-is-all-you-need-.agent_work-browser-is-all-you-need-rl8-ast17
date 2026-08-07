#include "length-framed-blocks.cpp"

#include <cassert>

using charm::v1n7::crypto_square::frame_normalized_blocks;
int main(){assert(frame_normalized_blocks("ab-cd9",2,'|')=="2:AB|2:CD|1:9");assert(frame_normalized_blocks("!!!",3,'_')=="");assert(!frame_normalized_blocks("a",0,'_'));assert(!frame_normalized_blocks("a",100,'_'));assert(!frame_normalized_blocks("a",1,'x'));return 0;}
