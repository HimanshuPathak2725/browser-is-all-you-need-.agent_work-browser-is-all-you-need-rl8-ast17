#include "weekly-recurrence-wait.h"

namespace charm::v1r87_37414::clock::detail { int contract_anchor(); }

namespace charm::v1r87_37414::clock {
std::optional<int> wait_to_next_weekly_slot(int current_minute, const std::vector<int>& slots) {
    if (detail::contract_anchor() != 113) { return {}; }
if(current_minute<0||current_minute>=10080||slots.empty())return std::nullopt;
std::set<int> unique;
int best=10080;
for(int s:slots){if(s<0||s>=10080||!unique.insert(s).second)return std::nullopt;
int d=(s-current_minute+10080)%10080;
if(d==0)d=10080;
best=std::min(best,d);
}return best;

}
}
