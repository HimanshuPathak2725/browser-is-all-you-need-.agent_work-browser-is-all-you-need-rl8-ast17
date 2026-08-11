# Objective

Fix overflow when fmt formats
`std::chrono::time_point<std::chrono::system_clock, Duration>` values whose
`Duration` can represent instants outside the native system-clock duration range.
Solve the general conversion problem; do not special-case an example date or
hardcode formatted output.

# Failure reproduction

On the evaluator's 64-bit Linux C++11 configuration, this must format as
`3000-01-01` with `{:%Y-%m-%d}`:

```cpp
using time_point = std::chrono::time_point<std::chrono::system_clock,
                                           std::chrono::milliseconds>;
time_point value{std::chrono::seconds(32503680000LL)};
```

The old route narrows through `system_clock::duration` and
`system_clock::to_time_t()` before calendar conversion. That intermediate narrowing
can overflow even though the source duration and platform `time_t` can represent the
instant.

# Required behavior

- Convert system-clock time points to `time_t` directly from
  `time_point.time_since_epoch()` without native-clock-duration narrowing.
- Preserve large positive and negative epochs, normal dates, fractional seconds,
  integral and floating representations, mixed representations, coarse periods, and
  feature-gated local-time formatting.
- With `FMT_SAFE_DURATION_CAST` enabled, an unrepresentable same-category conversion
  must throw `fmt::format_error("cannot format duration")`; it must not wrap.
- Preserve the existing negative-remainder adjustment and `duration is too small`
  guard.

# Compatibility and invariants

Preserve public APIs, error behavior, thread safety, locale behavior, feature guards,
and C++11 compatibility. Keep representation and period generic. Do not add global
state, undefined signed overflow, platform-only shortcuts, unconstrained competing
overloads, `if constexpr`, concepts, `requires`, or other C++14-or-newer syntax.

# Editable scope

Modify only `include/fmt/chrono.h`. Do not modify tests, build files, documentation,
generated files, vendored files, `include/fmt/format.h`, or any other path.

# Validation expectations

The harness—not the model—performs the scope check, warning-clean C++11 compilation,
chrono regression execution, and independent runtime verification. Do not claim that
you compiled or tested the change. If the first attempt fails compilation, one later
turn may expose only the first sanitized diagnostic rooted in the editable header.

# Response contract

Work through Aider's diff-editing interface. Make one coherent production edit and
return only applicable Aider diff edits, not prose. Use exact current file text in
SEARCH blocks and keep each block narrow enough to avoid consuming a neighboring
function, namespace boundary, brace, or preprocessor directive.

# Intern guide: file map and repair order

The important lexical regions, in file order, are:

| Region | Contents | Required action |
|---|---|---|
| Header and feature flags | Includes and `FMT_SAFE_DURATION_CAST` | Preserve. |
| `safe_duration_cast` namespace | Checked same-category duration conversions | Reuse; do not move or rewrite. |
| First `namespace detail` | Internal time and locale helpers, ending immediately before `FMT_BEGIN_EXPORT` | Insert the three new helper items here. |
| Exported calendar overloads | `localtime` and `gmtime` overloads | Route generic time points through `detail::to_time_t`. |
| Later `namespace detail` and formatters | Fractional, millisecond, duration, system-clock, and local-time consumers | Migrate every named cast/call site. |

Follow the order below. Declaration order and lexical namespace are compile-critical.

## Priority 0: add the helper block at the exact anchor

In the already-open **first** `namespace detail`, insert this complete contiguous block
after the existing `write(...)` overloads and immediately before the closing
`}  // namespace detail` that directly precedes `FMT_BEGIN_EXPORT`:

```cpp
template <typename Rep1, typename Rep2>
struct is_same_arithmetic_type
    : public std::integral_constant<bool,
                                    (std::is_integral<Rep1>::value &&
                                     std::is_integral<Rep2>::value) ||
                                        (std::is_floating_point<Rep1>::value &&
                                         std::is_floating_point<Rep2>::value)> {
};

template <
    typename To, typename FromRep, typename FromPeriod,
    FMT_ENABLE_IF(is_same_arithmetic_type<FromRep, typename To::rep>::value)>
To fmt_duration_cast(std::chrono::duration<FromRep, FromPeriod> from) {
#if FMT_SAFE_DURATION_CAST
  int ec;
  To to = safe_duration_cast::safe_duration_cast<To>(from, ec);
  if (ec) FMT_THROW(format_error("cannot format duration"));
  return to;
#else
  return std::chrono::duration_cast<To>(from);
#endif
}

template <
    typename To, typename FromRep, typename FromPeriod,
    FMT_ENABLE_IF(!is_same_arithmetic_type<FromRep, typename To::rep>::value)>
To fmt_duration_cast(std::chrono::duration<FromRep, FromPeriod> from) {
  return std::chrono::duration_cast<To>(from);
}

template <typename Duration>
std::time_t to_time_t(
    std::chrono::time_point<std::chrono::system_clock, Duration> time_point) {
  return fmt_duration_cast<std::chrono::duration<std::time_t>>(
             time_point.time_since_epoch())
      .count();
}
```

Do not create a new namespace around this block. Do not place it before the first
`namespace detail` opening, after that namespace closes, or in a later reopening.
The `template <typename Duration>` line immediately above `to_time_t` is mandatory.

## Priority 0: make the exported calendar overloads generic

Keep `gmtime(std::time_t)` unchanged. Replace only the system-clock time-point overload
with:

```cpp
template <typename Duration>
inline std::tm gmtime(
    std::chrono::time_point<std::chrono::system_clock, Duration> time_point) {
  return gmtime(detail::to_time_t(time_point));
}
```

In the existing `FMT_USE_LOCAL_TIME` overload, preserve its template and feature guard
but return:

```cpp
return localtime(
    detail::to_time_t(std::chrono::current_zone()->to_sys(time)));
```

The helpers are members of `detail`; these exported overloads are outside `detail` and
must use `detail::to_time_t`.

## Priority 1: migrate every consumer

Complete this finite ledger without redesigning surrounding functions:

| Consumer | Required edit |
|---|---|
| `write_fractional_seconds` | Use `d - fmt_duration_cast<std::chrono::seconds>(d)` and `fmt_duration_cast<subsecond_precision>(fractional).count()`. |
| Old helper | Delete the complete `#if FMT_SAFE_DURATION_CAST` definition of `fmt_safe_duration_cast`, but only after replacing all its consumers. |
| Integral `get_milliseconds` | In the safe branch, replace all three old helper calls with `fmt_duration_cast`; in the fallback branch use `fmt_duration_cast<std::chrono::seconds>(d)` and `fmt_duration_cast<std::chrono::milliseconds>(d - s)`. Preserve both branches, returns, braces, and `#endif`. |
| `chrono_formatter` seconds assignment | Replace the macro-specific assignment branch with `s = fmt_duration_cast<seconds>(std::chrono::duration<rep, Period>(val));`. |
| System-clock formatter | Use `detail::fmt_duration_cast` for the nested fractional calculation and one-second conversion. Use `do_format(gmtime(val), ctx, &subsecs)` and `format(gmtime(val), ctx)`. |
| Guarded local-time formatter | Mirror the nested `detail::fmt_duration_cast` calculation. Use `do_format(localtime(val), ctx, &subsecs)` and `format(localtime(val), ctx)`. |

The system-clock calculation must retain this exact nesting:

```cpp
auto subsecs = detail::fmt_duration_cast<Duration>(
    epoch - detail::fmt_duration_cast<std::chrono::seconds>(epoch));
auto second = detail::fmt_duration_cast<Duration>(std::chrono::seconds(1));
```

Inside a `namespace detail` region, call `fmt_duration_cast` without a `detail::`
prefix. Formatter specializations outside `detail` must call
`detail::fmt_duration_cast`. Do not infer scope from nearby comments; check the actual
namespace braces.

## Priority 2: preserve fragile structure

Do not remove, retype, rename, alias, or change the bodies or declaration kind of these
callable portability fallbacks:

- `localtime_r FMT_NOMACRO(...)`
- `localtime_s(...)`
- `gmtime_r(...)`
- `gmtime_s(...)`

Preserve all neighboring function boundaries and every existing `#if`, `#else`, and
`#endif`. In particular, do not let an Aider SEARCH block cross the
`get_milliseconds` function boundary or delete its fallback return path.

# Why the prior attempts failed

Treat these as compile blockers, not optional advice:

1. **`Duration` not declared:** every signature using `Duration` must have a visible
   `template <typename Duration>` declaration. This applies independently to
   `to_time_t` and the generic `gmtime` overload.
2. **`fmt_duration_cast` not declared:** define both overloads before their first use,
   inside the first `detail` namespace at the exact pre-`FMT_BEGIN_EXPORT` anchor.
3. **`to_time_t` not a member of `detail`:** the helper must be physically enclosed by
   `namespace detail { ... }`; exported callers must use `detail::to_time_t`.
4. **Wrong helper argument:** call `to_time_t` with a system-clock `time_point`, never
   with a bare duration. Only `fmt_duration_cast` accepts a duration.
5. **Broken header structure:** retain all `#endif` directives, braces, overloads, and
   return paths; later parser errors are often cascades from an earlier deleted boundary.

# Priority-ordered final checks

Perform these checks in order; stop and correct the patch at the first failed check:

1. [P01] Scope: the Git change is nonempty and touches only `include/fmt/chrono.h`.
2. [P02] Declarations: the trait, both SFINAE cast overloads, and templated `to_time_t`
   form one contiguous block inside the first `detail` namespace before
   `FMT_BEGIN_EXPORT`; every `Duration` is visibly declared.
3. [P03] Lookup: helper calls are unqualified inside `detail` and `detail::`-qualified
   outside it; `to_time_t` receives a `time_point`, not a duration.
4. [P04] Calendar roots: the generic exported `gmtime` and guarded `localtime` use
   `detail::to_time_t`; both formatter branches call `gmtime(val)` or `localtime(val)`
   directly, with no preceding `time_point_cast<seconds>`.
5. [P05] Consumer ledger: both fractional casts, every millisecond cast in both macro
   branches, the chrono-formatter seconds assignment, and all system/local time-point
   subsecond and one-second casts use the new helper with correct qualification.
6. [P06] Structure: the obsolete helper is gone, but all fallbacks, overloads,
   preprocessor directives, namespace/function braces, negative adjustment, error guard,
   and return paths remain intact.
7. [P07] Language and overloads: the patch is C++11-compatible, uses the exact two
   mutually exclusive SFINAE overloads, and adds no unconstrained fallback.
8. [P08] Output: return applicable Aider diff edits only and make no compilation or test
   claim; the harness performs execution after the response.
