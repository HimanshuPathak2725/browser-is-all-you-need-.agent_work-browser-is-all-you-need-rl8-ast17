#include "escrow-tranche-replay.h"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::bank_account;
int main() {
require_case(replay_escrow_tranches({{"a",7,false},{"a",2,true}}).value()==std::map<std::string,std::int64_t>{{"a",5}});
require_case(replay_escrow_tranches({{"a",3,false},{"a",3,true}}).value().empty());
require_case(!replay_escrow_tranches({{"a",1,true}}));
require_case(!replay_escrow_tranches({{"",1,false}}));
require_case(!replay_escrow_tranches({{"a",0,false}}));
return 0;
}
