#include "deterministic-shard-top-letter.h"

#include <cassert>

using charm::v1n7::parallel_letter_frequency::parallel_top_lowercase;
int main(){auto r=parallel_top_lowercase({"bba","acc"},2);assert((r&&*r&&**r==std::pair<char,std::size_t>('a',2)));auto e=parallel_top_lowercase({"ABC"},1);assert(e&&!*e);assert(!parallel_top_lowercase({},0));auto n=parallel_top_lowercase({},2);assert(n&&!*n);assert(parallel_top_lowercase({"zz"},9)->value().first=='z');return 0;}
