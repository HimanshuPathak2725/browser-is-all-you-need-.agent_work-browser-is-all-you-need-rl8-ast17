#include "typed-plant-row-parser.h"

#include <cassert>

using namespace charm::v1n7::kindergarten_garden;
int main(){auto r=parse_typed_garden("RCGV","GCVR",{"Ada","Bob"});assert(r&&r->size()==2&&r->at(0).second[0]==PlantCode::radish&&r->at(1).first=="Bob");assert(parse_typed_garden("","",{})->empty());assert(!parse_typed_garden("C","C",{}));assert(!parse_typed_garden("XX","CC",{"A"}));assert(!parse_typed_garden("CC","GG",{"A","B"}));return 0;}
