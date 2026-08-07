# Account lifecycle machine

Implement the C++17 task in `account-lifecycle-machine.h`, `account-lifecycle-machine.cpp`, `account-lifecycle-machine_detail.cpp`. Replay an account lifecycle beginning closed. open requires a nonnegative opening balance, credit and debit require an open account and positive amounts, debit may not overdraw, and close requires a zero balance. Any invalid transition rejects the entire trace. Return final balance, open flag, and number of completed closures.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::bank_account {
enum class AccountAction { open, credit, debit, close }; struct AccountEvent { AccountAction action; long long cents; };
std::optional<std::array<long long,3>> replay_account_lifecycle(const std::vector<AccountEvent>& events);
}
```

Required edge behavior:

- opening twice rejects
- money actions require open state
- overdraft rejects
- close requires zero
- overflow rejects

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
