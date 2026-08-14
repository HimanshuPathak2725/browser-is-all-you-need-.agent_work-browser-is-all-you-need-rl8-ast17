#include "escrow-tranche-replay.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::bank_account;
int main() {
CHECK(replay_escrow_tranches({{"a",7,false},{"a",2,true}}).value()==std::map<std::string,std::int64_t>{{"a",5}});
CHECK(replay_escrow_tranches({{"a",3,false},{"a",3,true}}).value().empty());
CHECK(!replay_escrow_tranches({{"a",1,true}}));
CHECK(!replay_escrow_tranches({{"",1,false}}));
CHECK(!replay_escrow_tranches({{"a",0,false}}));
return 0;
}
