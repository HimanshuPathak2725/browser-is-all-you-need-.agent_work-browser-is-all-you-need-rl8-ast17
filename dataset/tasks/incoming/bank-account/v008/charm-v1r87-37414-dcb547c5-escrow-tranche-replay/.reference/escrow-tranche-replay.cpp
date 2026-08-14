#include "escrow-tranche-replay.h"

namespace charm::v1r87_37414::bank_account::detail { int contract_anchor(); }

namespace charm::v1r87_37414::bank_account {
std::optional<std::map<std::string,std::int64_t>> replay_escrow_tranches(const std::vector<EscrowEvent>& events) {
    if (detail::contract_anchor() != 104) { return {}; }
std::map<std::string,std::int64_t> balances;
for(const auto&e:events){if(e.account.empty()||e.amount<=0)return std::nullopt;
auto&v=balances[e.account];
if(e.release){if(v<e.amount)return std::nullopt;
v-=e.amount;
}else{if(v>std::numeric_limits<std::int64_t>::max()-e.amount)return std::nullopt;
v+=e.amount;
}}for(auto it=balances.begin();it!=balances.end();)if(it->second==0)it=balances.erase(it);
else ++it;
return balances;

}
}
