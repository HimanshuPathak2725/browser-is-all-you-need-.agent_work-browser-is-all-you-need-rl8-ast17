#include "explicit-contiguous-relation.h"

charm::v1n7::sublist::SequenceRelation charm::v1n7::sublist::classify_contiguous_relation(const std::vector<int>& first,const std::vector<int>& second){if(first==second)return SequenceRelation::equal;auto contains=[](const std::vector<int>& haystack,const std::vector<int>& needle){return std::search(haystack.begin(),haystack.end(),needle.begin(),needle.end())!=haystack.end();};if(contains(second,first))return SequenceRelation::proper_sublist;if(contains(first,second))return SequenceRelation::proper_superlist;return SequenceRelation::unrelated;}
