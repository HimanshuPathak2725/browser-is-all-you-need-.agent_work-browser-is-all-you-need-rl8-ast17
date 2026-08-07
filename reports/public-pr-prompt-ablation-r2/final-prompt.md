# Objective

Correct chrono formatting for `std::chrono::time_point<std::chrono::system_clock,
Duration>` when `Duration` can represent calendar instants outside the range of the
clock's native duration. Solve the general conversion problem. Do not special-case an
example date or hardcode formatted output.

# Model and evaluator boundary

You receive the relevant repository files through Aider's diff-editing interface. You
do not have an interactive terminal, arbitrary repository search, network access, or
compiler feedback during this response. Do not claim that you compiled or tested the
change. The evaluator will compile after your response.

Use only the supplied file contents and make one coherent production edit. If an Aider
edit block needs correction, correct only that block against the current file text. Do
not reinterpret or change unrelated marked lines.

# Failure reproduction

On the evaluator's 64-bit Linux C++11 configuration, this value must format as
`3000-01-01` with `{:%Y-%m-%d}`:

```cpp
using time_point = std::chrono::time_point<std::chrono::system_clock,
                                           std::chrono::milliseconds>;
time_point value{std::chrono::seconds(32503680000LL)};
```

The current path narrows through the native `system_clock::duration` before calendar
conversion. That intermediate conversion can overflow even when the source duration
and platform calendar conversion can represent the instant.

# Required behavior

- Avoid native-clock-duration narrowing for wide or coarse system-clock time points.
- Preserve large positive and negative epochs, ordinary dates, and fractional seconds.
- Preserve integral, floating-point, mixed-representation, and coarse-duration behavior.
- Preserve feature-gated local-time formatting.
- When `FMT_SAFE_DURATION_CAST` is enabled, reject an unrepresentable checked
  same-category conversion with `fmt::format_error`; do not wrap.
- Preserve public APIs, error compatibility, thread safety, locale behavior, and C++11
  compatibility.

# Compatibility and invariants

Preserve public APIs, existing error behavior, thread safety, locale behavior,
feature guards, and C++11 compatibility. Keep duration representation and period
generic. Do not introduce global state, undefined signed overflow, platform-only
shortcuts, or C++14-or-newer syntax.

# Editable scope

Modify only `include/fmt/chrono.h`. Do not modify tests, build files, documentation,
generated files, vendored files, `include/fmt/format.h`, or any other path.

Return only applicable Aider diff edits. Do not return prose instead of an edit. Keep
each edit block narrow enough that it cannot accidentally consume a neighboring
function, overload, namespace boundary, or preprocessor directive.

# Validation expectations

The harness, not the model, performs scope checks, a warning-clean C++11 chrono
build, regression execution, and an independent runtime probe after the response.
If the first candidate fails compilation, one later turn may provide only the first
sanitized diagnostic rooted in the editable header.

# Response contract

You receive relevant repository files through Aider diff editing. Make one coherent
production edit and return applicable Aider diff edits, not prose. Keep edit blocks
narrow enough that they cannot consume a neighboring function, overload, namespace
boundary, or preprocessor directive.

# Implementation map

Implement one unified duration-conversion route and migrate every named consumer below.

## 1. Conversion helpers

- Define the arithmetic-category trait and unified duration-cast helper lexically inside
  `namespace detail`.
- Insert the helper block inside the already-open first `namespace detail`,
  immediately before its closing `}  // namespace detail` that directly precedes
  `FMT_BEGIN_EXPORT`. Do not insert it before the namespace opening.
- This anchor is after the safe-duration-cast implementation is visible and before
  exported calendar functions use the helpers.
- Same-category means integral/integral or floating/floating, even when the exact C++
  types differ.
- Use two mutually exclusive C++11 SFINAE paths:
  - same-category conversion uses the existing checked machinery when
    `FMT_SAFE_DURATION_CAST` is enabled and standard `duration_cast` otherwise;
  - mixed-category conversion always uses standard `duration_cast`.
- Do not add an unconstrained overload that can compete with those two paths.
- Define the direct system-clock-to-`time_t` helper in the same `detail` namespace.
  Its signature must declare `template <typename Duration>`, and its conversion must
  begin from `time_point.time_since_epoch()`, not from
  `system_clock::to_time_t` or a native-duration time-point cast.

Lexical-scope invariant: a caller written as `detail::fmt_duration_cast` or
`detail::to_time_t` must resolve to a definition physically enclosed by
`namespace detail { ... }`. Do not insert those definitions immediately before the
namespace opening.

### Exact helper bodies

Use these helper bodies without changing their semantics:

```cpp
template <typename Rep1, typename Rep2>
struct is_same_arithmetic_type
    : public std::integral_constant<
          bool,
          (std::is_integral<Rep1>::value && std::is_integral<Rep2>::value) ||
              (std::is_floating_point<Rep1>::value &&
               std::is_floating_point<Rep2>::value)> {};
```

```cpp
template <typename To, typename FromRep, typename FromPeriod,
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
```

```cpp
template <typename To, typename FromRep, typename FromPeriod,
          FMT_ENABLE_IF(!is_same_arithmetic_type<FromRep, typename To::rep>::value)>
To fmt_duration_cast(std::chrono::duration<FromRep, FromPeriod> from) {
  return std::chrono::duration_cast<To>(from);
}
```

```cpp
template <typename Duration>
std::time_t to_time_t(
    std::chrono::time_point<std::chrono::system_clock, Duration> time_point) {
  return fmt_duration_cast<std::chrono::duration<std::time_t>>(
             time_point.time_since_epoch())
      .count();
}
```

## 2. Calendar conversion overloads

- Make the system-clock `gmtime` time-point overload generic over `Duration`.
- Declare its `Duration` template parameter explicitly.
- Return `gmtime(detail::to_time_t(time_point))`.
- Preserve the `std::time_t` overload and its platform behavior.
- In the `FMT_USE_LOCAL_TIME` path, route the converted system-clock time point
  through the same direct helper without changing timezone semantics or feature guards.

## 3. Finite consumer migration

Migrate all of these sites to the unified helper while preserving their surrounding
control flow:

1. both conversions in `write_fractional_seconds`;
2. all whole-second and millisecond-remainder conversions in both
   `get_milliseconds` macro branches;
3. the seconds construction in `chrono_formatter`;
4. the fractional and one-second conversions in the system-clock time-point formatter;
5. the equivalent conversions in the local-time formatter.

Only after every consumer is migrated, remove the obsolete legacy duration-cast helper.

## 4. Root-path correction

- In both fractional and non-fractional system-clock formatter paths, pass the original
  `val` to the generic calendar conversion. Do not narrow it first with
  `time_point_cast<seconds>`.
- Mirror the same direct-call correction for both local-time formatter paths.
- Preserve the existing no-subseconds dispatch through
  `formatter<std::tm, Char>::format`.
- Preserve the existing fractional dispatch, negative-remainder handling, and
  `duration is too small` guard.
- Preserve `do_format(gmtime(val), ctx, &subsecs)` in the fractional
  system-clock path and `format(gmtime(val), ctx)` in the no-subseconds
  path. Mirror those calls with `localtime(val)` in the guarded local-time
  formatter.

# Do-not-change invariants

The following declarations are deliberate callable fallback overloads used for
portability and overload detection:

- `localtime_r FMT_NOMACRO(...)`
- `localtime_s(...)`
- `gmtime_r(...)`
- `gmtime_s(...)`

Do not remove, retype, alias, rename, or change the bodies or declaration kind of those
functions. Preserve `FMT_NOMACRO` behavior.

Also preserve:

- every existing `#if`, `#else`, and `#endif` surrounding changed code;
- every neighboring function and overload boundary;
- namespace openings and closings;
- both enabled and disabled `FMT_SAFE_DURATION_CAST` branches;
- the `FMT_USE_LOCAL_TIME` feature guard;
- C++11 syntax: no deduced function return types, `if constexpr`, concepts,
  `requires`, or other newer-language features.

# Final patch audit

Before emitting the edit, inspect the proposed patch itself and ensure all of these are
true:

1. [C01] Only `include/fmt/chrono.h` changes.
2. [C02] Every new signature type is declared by a visible template parameter or declaration.
3. [C03] New helper definitions are inside `detail`, and every call uses the qualification
   appropriate to its lexical scope.
4. [C04] The four callable time fallbacks are byte-for-byte unchanged.
5. [C05] No changed hunk deletes or crosses an unmatched `#if/#else/#endif`, namespace
   boundary, function brace, or neighboring overload.
6. [C06] Both fractional conversion sites and both millisecond macro branches are migrated.
7. [C07] The obsolete helper is removed only after its last consumer is migrated.
8. [C08] No `time_point_cast<seconds>` remains before the system-clock or local-time calendar
   conversion.
9. [C09] No C++14-or-newer syntax is introduced.
10. [C10] Do not claim compilation or test success; execution occurs after the response.
