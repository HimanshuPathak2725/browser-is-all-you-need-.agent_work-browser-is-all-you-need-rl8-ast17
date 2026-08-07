# Idempotent cent ledger

Implement the C++17 task in `idempotent-cent-ledger.h`, `idempotent-cent-ledger.cpp`, `idempotent-cent-ledger_detail.cpp`. Apply uniquely identified cent transactions exactly once, reject any transition below zero atomically, and preserve accepted-ID order.

The exact public API is:

```cpp
namespace charm::bank { class CentLedger { public: bool apply(std::string,long long); long long balance() const; std::vector<std::string> accepted_ids() const; }; }
```

Required edge behavior:

- empty identifiers are invalid
- duplicate IDs do not apply twice
- an exact withdrawal reaches zero
- overflow and overdraft leave all state unchanged
- a zero delta is accepted once

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
