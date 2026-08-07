# Atomic allergen dose policy

Complete the existing C++17 implementation in `dose-policy-table.cpp`. The file
itself is the public include surface and must define `charm::allergy::DosePolicyTable`.

`set_limit(name, limit)` stores or replaces a nonnegative cumulative dose limit
for a non-empty allergen name and returns `true`; invalid inputs return `false`
without changing the table. `exceeded(batch)` first validates every pair: an
empty name or negative dose invalidates the entire batch and yields an empty
result. Otherwise aggregate repeated names. Names with no configured limit are
ignored. Return configured names whose aggregate dose is strictly greater than
their limit, in ascending bytewise lexical order. The call is read-only.

Required API:

```cpp
class DosePolicyTable {
public:
    bool set_limit(std::string name, int limit);
    std::vector<std::string> exceeded(
        const std::vector<std::pair<std::string, int>>& batch) const;
};
```

Keep every method inline in this single editable `.cpp` file so it can be used
as an include surface. Use no external dependencies.
