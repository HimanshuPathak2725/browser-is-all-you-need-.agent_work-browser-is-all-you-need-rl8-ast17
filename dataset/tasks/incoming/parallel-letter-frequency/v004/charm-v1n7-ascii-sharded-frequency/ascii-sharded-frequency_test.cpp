#include "ascii-sharded-frequency.h"

#include <cassert>

using charm::v1n7::parallel_letter_frequency::sharded_ascii_frequency;
int main(){auto r=sharded_ascii_frequency({"Aa!","bA","Ã©"},2);assert(r&&r->at('a')==3&&r->at('b')==1&&r->size()==2);assert(sharded_ascii_frequency({},3)->empty());assert(!sharded_ascii_frequency({},0));assert(sharded_ascii_frequency({"123"},1)->empty());assert(sharded_ascii_frequency({"Z"},9)->at('z')==1);return 0;}
