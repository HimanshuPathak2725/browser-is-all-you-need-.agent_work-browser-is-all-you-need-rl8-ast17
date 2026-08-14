# Billing pulse summary

Implement the C++17 task in `billing-pulse-summary.cpp`. Bill positive-duration calls by positive whole-second pulses, rounding each call independently upward. Calls name nonempty accounts and have end greater than start; aggregate pulse counts with overflow checks.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::phone_number {
struct TimedCall { std::string account; std::int64_t start_second; std::int64_t end_second; };
std::optional<std::map<std::string,std::int64_t>> summarize_billing_pulses(const std::vector<TimedCall>& calls, std::int64_t pulse_seconds);
}
```

Required edge behavior:

- pulse size is positive
- accounts are nonempty
- times are nonnegative and increasing
- each call rounds independently
- account totals are checked

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
