# Atomic transfer batch

Implement the C++17 task in `atomic-transfer-batch.cpp`. Apply a batch of positive transfers to a unique-name balance table. Every endpoint must exist and differ, no transfer may overdraw, and arithmetic overflow rejects. The operation is atomic: return no result on any failure; otherwise return balances in lexical account order.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::bank_account {
struct Transfer { std::string from; std::string to; long long cents; };
std::optional<std::vector<std::pair<std::string,long long>>> settle_transfer_batch(const std::vector<std::pair<std::string,long long>>& balances, const std::vector<Transfer>& transfers);
}
```

Required edge behavior:

- accounts are unique
- amounts are positive
- self-transfer rejects
- batch failure is atomic
- output order is lexical

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
