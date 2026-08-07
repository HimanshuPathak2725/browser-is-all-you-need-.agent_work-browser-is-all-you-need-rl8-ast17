#include "conflict-aware-transcript-merge.h"

#include <cassert>

using namespace charm::v1n7::grade_school;
int main(){auto r=merge_identical_transcripts({{"b",2,8},{"a",1,9}},{{"a",1,9},{"c",3,7}});assert(r&&r->size()==3&&r->at(0).id=="a");assert(merge_identical_transcripts({},{})->empty());assert(!merge_identical_transcripts({{"a",1,1}},{{"a",2,1}}));assert(!merge_identical_transcripts({{"a",1,1},{"a",1,2}},{}));assert(!merge_identical_transcripts({{"",1,1}},{}));return 0;}
