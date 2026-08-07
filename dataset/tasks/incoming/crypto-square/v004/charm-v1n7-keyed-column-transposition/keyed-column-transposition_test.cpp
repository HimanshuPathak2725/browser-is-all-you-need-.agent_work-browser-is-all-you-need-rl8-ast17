#include "keyed-column-transposition.h"

#include <cassert>

using charm::v1n7::crypto_square::keyed_column_encode;
int main(){assert(keyed_column_encode("A b-c!","ba",'_')=="b_ac");assert(keyed_column_encode("", "x", '_')=="");assert(!keyed_column_encode("x","",'_'));assert(!keyed_column_encode("x","a-",'_'));assert(!keyed_column_encode("x","a",'7'));return 0;}
