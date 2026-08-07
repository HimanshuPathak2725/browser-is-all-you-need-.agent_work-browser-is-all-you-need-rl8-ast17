# Atomic transfer plan

Implement the C++17 task in `atomic-transfer-plan.cpp`. Construct a book from named balances, validate a whole transfer plan, simulate aggregate deltas, and commit only when every final balance is valid.

The exact public API is:

```cpp
namespace charm::bank { struct Transfer { std::string from; std::string to; long long cents; }; class AccountBook { public: explicit AccountBook(std::map<std::string,long long>); bool execute(const std::vector<Transfer>&); long long balance_of(std::string_view) const; }; }
```

Required edge behavior:

- an empty plan succeeds
- unknown accounts reject atomically
- negative amounts reject
- chained funding is based on aggregate final balances
- self-transfer has no net effect

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
