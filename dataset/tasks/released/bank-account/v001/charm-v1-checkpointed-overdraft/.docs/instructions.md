# Checkpointed overdraft repair

Implement the C++17 task in `checkpointed-overdraft.hpp`. Track balance and overdraft-fee count in checkpoints. Rejected withdrawals change nothing; rollback restores both fields and truncates later checkpoints.

The exact public API is:

```cpp
namespace charm::bank { class CheckpointAccount { public: CheckpointAccount(long long,long long,long long); std::size_t checkpoint(); bool withdraw(long long); void deposit(long long); bool rollback(std::size_t); long long balance() const; std::size_t fee_count() const; }; }
```

Required edge behavior:

- negative deposits are ignored
- exact-balance withdrawal charges no fee
- crossing below zero charges one fee
- invalid rollback is inert
- rollback may be repeated for the retained checkpoint

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
