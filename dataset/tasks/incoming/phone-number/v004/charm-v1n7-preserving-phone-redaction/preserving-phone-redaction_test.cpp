#include "preserving-phone-redaction.cpp"

#include <cassert>

using charm::v1n7::phone_number::redact_phone_digits;
int main(){auto r=redact_phone_digits("(223) 456-7890",4,'*');assert(r&&r->text=="(***) ***-7890"&&r->masked_digits==6);auto none=redact_phone_digits("abc",0,'#');assert(none&&none->text=="abc"&&none->masked_digits==0);auto visible=redact_phone_digits("12",2,'#');assert(visible&&visible->text=="12"&&visible->masked_digits==0);assert(!redact_phone_digits("12",3,'#'));assert(!redact_phone_digits("12",1,'7'));return 0;}
