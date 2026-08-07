# Rolling exposure ledger

Implement the exact public API in `exposure-window-ledger.h` and its two source
files, all in namespace `charm::allergy`.

`ExposureWindowLedger::record(name, severity, minute)` appends an immutable
event when `name` is non-empty and `severity` is nonnegative; otherwise it does
nothing. `active(minimum_severity, now, horizon)` returns the distinct allergen
names having at least one recorded event whose severity is at least the
threshold and whose minute is in the inclusive interval
`[now - horizon, now]`. A negative horizon returns an empty vector. Future
events do not qualify. Return names in ascending bytewise lexical order.

The required signatures are:

```cpp
class ExposureWindowLedger {
public:
    void record(std::string name, int severity, int minute);
    std::vector<std::string> active(int minimum_severity,
                                    int now,
                                    int horizon) const;
};
```

Use only C++17 standard-library facilities. Preserve the exact namespace,
class name, signatures, const qualifier, and file names.
