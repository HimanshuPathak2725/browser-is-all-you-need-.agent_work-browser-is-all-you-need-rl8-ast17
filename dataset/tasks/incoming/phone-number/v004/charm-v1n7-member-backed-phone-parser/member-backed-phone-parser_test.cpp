#include "member-backed-phone-parser.h"

#include <cassert>

using namespace charm::v1n7::phone_number;
int main(){auto p=parse_normalized_phone("+1 (223) 456-7890 x42");assert(p&&p->digits()=="2234567890"&&p->extension()=="42");assert(parse_normalized_phone("2234567890")->extension().empty());assert(!parse_normalized_phone("1234567890"));assert(!parse_normalized_phone("2231567890"));assert(!parse_normalized_phone("2234567890x"));return 0;}
