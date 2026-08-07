#include "exact-clock-factory.h"

namespace charm::v1n7::clock::detail { int contract_anchor(); }

charm::v1n7::clock::ExactClock charm::v1n7::clock::make_exact_clock(long long hours, long long minutes) { long long value=(hours%24LL)*60LL+(minutes%1440LL);value%=1440LL;if(value<0)value+=1440LL;return ExactClock(static_cast<int>(value)); }
charm::v1n7::clock::ExactClock::ExactClock(int minute):minute_(minute){}
int charm::v1n7::clock::ExactClock::minutes_since_midnight() const{return minute_;}
charm::v1n7::clock::ExactClock charm::v1n7::clock::ExactClock::operator+(long long delta) const{return make_exact_clock(0,static_cast<long long>(minute_)+(delta%1440LL));}
bool charm::v1n7::clock::ExactClock::operator==(const ExactClock& other) const{return minute_==other.minute_;}
