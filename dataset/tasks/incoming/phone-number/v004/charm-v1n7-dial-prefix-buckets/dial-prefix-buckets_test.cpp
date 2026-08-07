#include "dial-prefix-buckets.h"

#include <cassert>

using charm::v1n7::phone_number::bucket_by_longest_prefix;
int main(){auto r=bucket_by_longest_prefix({"1202","1299","441"},{"1","12","44"});assert(r&&r->at("12")==std::vector<std::string>({"1202","1299"})&&r->at("44")==std::vector<std::string>({"441"}));assert(bucket_by_longest_prefix({},{})->empty());assert(!bucket_by_longest_prefix({"99"},{"1"}));assert(!bucket_by_longest_prefix({"1a"},{"1"}));assert(!bucket_by_longest_prefix({}, {"1","1"}));return 0;}
