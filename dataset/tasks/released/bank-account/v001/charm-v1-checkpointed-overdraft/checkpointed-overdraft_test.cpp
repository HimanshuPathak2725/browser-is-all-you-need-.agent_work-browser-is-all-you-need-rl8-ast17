#include "checkpointed-overdraft.hpp"
#include <cassert>
using charm::bank::CheckpointAccount;
int main() {
    CheckpointAccount account(20, 15, 2);
    const auto root = account.checkpoint();
    assert(account.withdraw(20) && account.balance() == 0 && account.fee_count() == 0);
    const auto zero = account.checkpoint();
    assert(account.withdraw(5) && account.balance() == -7 && account.fee_count() == 1);
    assert(!account.withdraw(20) && account.balance() == -7 && account.fee_count() == 1);
    assert(account.rollback(zero) && account.balance() == 0 && account.fee_count() == 0);
    account.deposit(4);
    assert(account.rollback(root) && account.balance() == 20);
    assert(!account.rollback(99));
    assert(account.rollback(root));
    CheckpointAccount boundary(0, 5, 2);
    assert(!boundary.withdraw(4) && boundary.balance() == 0 && boundary.fee_count() == 0);
    return 0;
}
