#include "best-declared-rule.cpp"

#include <cassert>

using charm::v1n7::yacht::best_declared_rule;
int main(){auto r=best_declared_rule({1,2,3,4,5},{"sum","full-run"});assert(r&&r->first=="full-run"&&r->second==30);assert(best_declared_rule({1,1,2,2,3},{"sum","three-match"})->first=="sum");assert(!best_declared_rule({1,2,3,4,5},{}));assert(!best_declared_rule({1,2,3,4,5},{"sum","sum"}));assert(!best_declared_rule({1,2,3,4,5},{"unknown"}));return 0;}
