#include "account-lifecycle-machine.h"

#include <cassert>

using namespace charm::v1n7::bank_account;
int main() {
    auto r=replay_account_lifecycle({{AccountAction::open,100},{AccountAction::debit,100},{AccountAction::close,0},{AccountAction::open,5}});
    assert(r && *r==(std::array<long long,3>{5,1,1}));
    assert(replay_account_lifecycle({})->at(1)==0);
    assert(!replay_account_lifecycle({{AccountAction::credit,1}}));
    assert(!replay_account_lifecycle({{AccountAction::open,1},{AccountAction::close,0}}));
    assert(!replay_account_lifecycle({{AccountAction::open,-1}}));
    return 0;
}
