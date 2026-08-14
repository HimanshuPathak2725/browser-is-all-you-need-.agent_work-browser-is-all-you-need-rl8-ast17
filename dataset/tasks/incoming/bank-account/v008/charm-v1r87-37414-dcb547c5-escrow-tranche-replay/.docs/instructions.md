# Escrow tranche replay

Implement the C++17 task in `escrow-tranche-replay.h`, `escrow-tranche-replay.cpp`, `escrow-tranche-replay_detail.cpp`. Replay account-scoped escrow deposits and releases. Amounts must be positive, a release may not exceed its account balance, and the result lists nonzero balances by account.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::bank_account {
struct EscrowEvent { std::string account; std::int64_t amount; bool release; };
std::optional<std::map<std::string,std::int64_t>> replay_escrow_tranches(const std::vector<EscrowEvent>& events);
}
```

Required edge behavior:

- amounts are strictly positive
- accounts are nonempty
- releases never overdraw
- overflow rejects
- zero final balances are omitted

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
