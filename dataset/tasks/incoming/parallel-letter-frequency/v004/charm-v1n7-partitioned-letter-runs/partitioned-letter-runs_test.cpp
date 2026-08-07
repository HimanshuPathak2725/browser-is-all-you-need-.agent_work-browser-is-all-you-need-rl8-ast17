#include "partitioned-letter-runs.cpp"

#include <cassert>

using charm::v1n7::parallel_letter_frequency::parallel_longest_letter_runs;
int main(){assert((parallel_longest_letter_runs({"aaA-bb","xyz","111"},2).value()==std::vector<std::size_t>{3,1,0}));assert(parallel_longest_letter_runs({},1)->empty());assert(!parallel_longest_letter_runs({"a"},0));assert(parallel_longest_letter_runs({"ZZ"},9)->at(0)==2);assert(parallel_longest_letter_runs({"aA"},1)->at(0)==2);return 0;}
