#include "explicit-contiguous-relation.h"

#include <cassert>

using namespace charm::v1n7::sublist;
int main(){assert(classify_contiguous_relation({1,2},{0,1,2,3})==SequenceRelation::proper_sublist);assert(classify_contiguous_relation({1,2},{1,2})==SequenceRelation::equal);assert(classify_contiguous_relation({1,2},{2,1})==SequenceRelation::unrelated);assert(classify_contiguous_relation({}, {1})==SequenceRelation::proper_sublist);assert(classify_contiguous_relation({1}, {})==SequenceRelation::proper_superlist);return 0;}
