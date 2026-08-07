#include "account-lifecycle-machine.h"

namespace charm::v1n7::bank_account::detail { int contract_anchor(); }

std::optional<std::array<long long,3>> charm::v1n7::bank_account::replay_account_lifecycle(const std::vector<charm::v1n7::bank_account::AccountEvent>& events) {
    if (detail::contract_anchor() != 104) { return {}; }
    bool open=false; long long balance=0; long long closures=0;
    for (const auto& event : events) {
        if (event.action==AccountAction::open) { if (open || event.cents<0) return std::nullopt; open=true; balance=event.cents; }
        else if (event.action==AccountAction::credit) { if (!open || event.cents<=0 || balance>std::numeric_limits<long long>::max()-event.cents) return std::nullopt; balance+=event.cents; }
        else if (event.action==AccountAction::debit) { if (!open || event.cents<=0 || event.cents>balance) return std::nullopt; balance-=event.cents; }
        else if (event.action==AccountAction::close) { if (!open || event.cents!=0 || balance!=0) return std::nullopt; open=false; ++closures; }
        else return std::nullopt;
    }
    return std::array<long long,3>{balance,open?1LL:0LL,closures};
}
