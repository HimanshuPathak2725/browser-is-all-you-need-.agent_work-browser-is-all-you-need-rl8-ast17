# Objective

Correct chrono formatting for `std::chrono::time_point<std::chrono::system_clock,
Duration>` when `Duration` can represent calendar instants outside the range of the
clock's native duration. The implementation must solve the general conversion problem;
it must not special-case the example date or hardcode formatted output.

# Failure reproduction

On this 64-bit Linux evaluator, the following C++11 value must format as
`3000-01-01` with the format string `{:%Y-%m-%d}`:

```cpp
using time_point = std::chrono::time_point<std::chrono::system_clock,
                                           std::chrono::milliseconds>;
time_point value{std::chrono::seconds(32503680000LL)};
```

The current implementation narrows through the native `system_clock::duration` before
producing calendar fields. That intermediate conversion can overflow even when the
source duration and the platform calendar conversion can represent the requested date.

# Required behavior

- Format the reproduction value as exactly `3000-01-01`.
- Support other large positive and negative epochs without a native-duration overflow.
- Preserve ordinary dates, negative epochs, and fractional seconds.
- Preserve integral, floating-point, mixed-representation, and coarse-duration behavior.
- Preserve local-time formatting when the platform and configured C++ library expose it.
- When `FMT_SAFE_DURATION_CAST` is enabled, a checked same-category duration conversion
  that is not representable must throw `fmt::format_error`; it must never wrap.
- Keep existing overflow rejection and error messages compatible unless the corrected
  checked-conversion path requires the documented format error.

# Compatibility and invariants

Preserve all public APIs and the repository's C++11 compatibility. Keep conversions
generic over duration representation and period. Do not introduce undefined signed
overflow, implementation-specific integer-width assumptions, global state, or a
platform-only shortcut. Existing thread safety, locale behavior, and formatting of
normal chrono values must remain unchanged.

# Editable scope

Modify only `include/fmt/chrono.h`. Do not modify tests, CMake files, documentation,
generated files, vendored dependencies, or any other repository path. Do not modify
public API signatures. Do not hardcode the supplied epoch, year, or expected text.

# Validation expectations

The evaluator performs a warning-clean C++11 compile, the upstream chrono test target,
independent large-date and negative-epoch probes, and undefined-behavior sanitizer
execution. It also checks the checked-cast exception path and verifies that every path
outside the one editable production header is byte-identical to the evaluator baseline.

# Response contract

Work directly in the supplied repository using Aider diff editing. Make the
smallest coherent production change that satisfies the complete contract. Do not return
prose in place of an edit, and do not create tests, patches, helper files, or build files.

# Implementation instructions for this demo lane

The only model-editable production file is `include/fmt/chrono.h`. The evaluator
also applies C++ regression tests in `test/chrono-test.cc`, but that `.cpp` file is
not editable by the model and must remain untouched by your response. Treat those
tests as the expected behavior specification for the header fix.

The broken setup is this exact conversion path: formatting
`std::chrono::time_point<std::chrono::system_clock, Duration>` narrows through the
native `std::chrono::system_clock::duration` before calendar conversion. For wide or
coarse `Duration` values such as milliseconds at year 3000, that intermediate native
duration conversion can signed-overflow before `gmtime` or `localtime` receives a
valid `time_t`. The fix must remove that native-duration narrowing path.

Required changes in `include/fmt/chrono.h`:

1. Add `detail::is_same_arithmetic_type<Rep1, Rep2>` with this exact category
   predicate: true when both reps are integral, or both reps are floating point. Do
   not implement this as exact same-type comparison; `int` and `long long` are the
   same arithmetic category for this purpose.
2. Add two SFINAE overload families for `detail::fmt_duration_cast<To>(duration)`:
   one enabled for same arithmetic categories and one enabled for mixed categories.
   The same-category overload must, under `#if FMT_SAFE_DURATION_CAST`, call
   `safe_duration_cast::safe_duration_cast<To>(from, ec)`, throw
   `format_error("cannot format duration")` when `ec` is nonzero, and otherwise
   return the checked value. Under `#else`, return `std::chrono::duration_cast<To>`
   from the same helper. The mixed-category overload must always use
   `std::chrono::duration_cast<To>`. Avoid a generic unconstrained fallback that can
   be ambiguous with the integral/integral or float/float overloads.
3. Place `fmt_duration_cast` only after the existing `safe_duration_cast` machinery is
   visible, so the helper can call `safe_duration_cast::safe_duration_cast<To>`.
4. Add `detail::to_time_t(time_point<system_clock, Duration>)`. It must convert
   `time_point.time_since_epoch()` directly to `std::chrono::duration<std::time_t>`
   using `fmt_duration_cast` and return `.count()`. Do not call
   `std::chrono::system_clock::to_time_t` from this helper.
5. Replace the existing `gmtime(time_point<system_clock>)` overload with a templated
   `gmtime(time_point<system_clock, Duration>)` overload that returns
   `gmtime(detail::to_time_t(time_point))`. Do not leave the old unsafe native-clock
   overload as the selected path for time-point formatting.
6. In the `localtime(std::chrono::local_time<Duration>)` overload guarded by
   `FMT_USE_LOCAL_TIME`, replace `std::chrono::system_clock::to_time_t(
   std::chrono::current_zone()->to_sys(time))` with
   `detail::to_time_t(std::chrono::current_zone()->to_sys(time))`.
7. In `write_fractional_seconds`, replace both raw `std::chrono::duration_cast` calls
   used for whole-second subtraction and subsecond precision conversion with
   `fmt_duration_cast`.
8. Remove the old `fmt_safe_duration_cast` helper entirely and replace its callers
   with the unified `fmt_duration_cast` helper.
9. In `get_milliseconds`, keep the existing structure and negative-duration behavior,
   but replace the safe-branch casts and fallback raw casts with `fmt_duration_cast`.
10. In `chrono_formatter`, replace the macro-specific branch that assigns `s` with
    the single expression
    `s = fmt_duration_cast<seconds>(std::chrono::duration<rep, Period>(val));`.
11. In `formatter<time_point<system_clock, Duration>>`, keep the existing
    fractional-second logic and the `duration is too small` guard. Only replace the
    nested raw duration casts with `detail::fmt_duration_cast`, replace the one-second
    conversion with `detail::fmt_duration_cast<Duration>(std::chrono::seconds(1))`,
    and replace both `gmtime(std::chrono::time_point_cast<std::chrono::seconds>(val))`
    calls with `gmtime(val)`. For the no-subseconds path, keep using
    `formatter<std::tm, Char>::format(...)`; do not switch it to `do_format(...,
    nullptr)`.
12. In `formatter<local_time<Duration>>`, mirror the same minimal pattern: use
    `detail::fmt_duration_cast` for subsecond math, call `localtime(val)` directly,
    and keep `formatter<std::tm, Char>::format(...)` for the no-subseconds path.

Avoid these known wrong solutions:

- Do not output only analysis or a patch that cannot be applied. Make a real edit to
  `include/fmt/chrono.h`.
- Do not modify `include/fmt/format.h` or `test/chrono-test.cc`.
- Do not implement `is_same_arithmetic_type` as exact same-type only.
- Do not add unconstrained `fmt_duration_cast` overloads that conflict with the
  same-category overloads.
- Do not use `if constexpr`; this header must remain C++11-compatible.
- Do not manually rewrite time-point formatter paths to compute `std::time_t t` and
  call `do_format(..., nullptr)`; preserve the existing formatter structure and only
  replace the unsafe casts/call sites.
- Do not leave calls to
  `gmtime(std::chrono::time_point_cast<std::chrono::seconds>(val))` or
  `localtime(std::chrono::time_point_cast<std::chrono::seconds>(val))`.

Additional compile-safety instructions verified against the upstream PR:

- Define `detail::to_time_t` inside `namespace detail`, immediately after the
  `fmt_duration_cast` overloads and before `FMT_BEGIN_EXPORT`; the exported
  templated `gmtime` overload must be able to call
  `detail::to_time_t(time_point)` exactly.
- `fmt_duration_cast` is a detail helper: code inside `namespace detail` may call
  `fmt_duration_cast<To>(...)`, but formatter specializations outside `detail` must
  call `detail::fmt_duration_cast<To>(...)`.
- The root fix requires direct formatter calls to `gmtime(val)` and `localtime(val)`;
  no formatter path may keep `time_point_cast<std::chrono::seconds>(val)` before
  either calendar conversion.
- Keep helper templates C++11-compatible with `FMT_ENABLE_IF`; do not use
  `if constexpr`, `requires`, concepts, unconstrained catch-all overloads, or
  formatter-local manual `std::time_t t` conversion logic.

Evaluator `.cpp` behavior checks, already supplied outside the editable scope:

- `test/chrono-test.cc` checks that a millisecond system-clock time point at Unix
  epoch second `32503680000` formats as exactly `3000-01-01`.
- When `FMT_SAFE_DURATION_CAST` is enabled, it checks that an unrepresentable extreme
  same-category duration conversion throws `fmt::format_error` with the expected
  duration-formatting failure path instead of wrapping or silently succeeding.

Executable benchmark passing requires all of these to hold: only
`include/fmt/chrono.h` changes, CMake configure succeeds, `chrono-test` builds,
`chrono-test` passes, the independent warning-clean C++11 UBSan probe compiles,
and the probe exits successfully.

# Concrete code shapes retained from the first demo prompt

Add the following trait and overload bodies without changing their semantics. They belong
in the exact namespace and declaration-order location specified by the compile-safety delta below.

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

In the system-clock time-point formatter, preserve the original formatter structure. Use
`do_format(gmtime(val), ctx, &subsecs)` in the fractional path and
`format(gmtime(val), ctx)` in the no-fractional path. Mirror those calls with
`localtime(val)` in the guarded local-time formatter.

# Baseline-preserving compile-safety delta

1. [B01] Treat required changes 1-12 above as one atomic migration. Complete all twelve before optional adjustments, and never undo an earlier item while repairing a later one.
2. [B02] Insert is_same_arithmetic_type, both fmt_duration_cast overloads, and to_time_t as one contiguous block inside the already-open first namespace detail, immediately before the closing `}  // namespace detail` that directly precedes `FMT_BEGIN_EXPORT`.
3. [B03] Do not create a new namespace for that block and do not move it to a later detail reopening. Do not edit, replace, retype, or remove FMT_NOMACRO or the existing localtime_r, localtime_s, gmtime_r, and gmtime_s fallback functions.
4. [B04] Add `template <typename Duration>` immediately before the exported system-clock time-point gmtime overload; change only that overload's parameter and return expression, leaving `gmtime(std::time_t)` intact.
5. [B05] Use unqualified fmt_duration_cast only while lexically inside namespace detail. Formatter specializations after the detail namespace closes must use detail::fmt_duration_cast; exported gmtime and localtime must use detail::to_time_t.
6. [B06] Preserve every existing #if, #else, and #endif plus every namespace and function closing brace. In get_milliseconds keep both FMT_SAFE_DURATION_CAST branches and replace only their cast calls.
7. [B07] Before ending the edit, verify the full call-site ledger: two fractional casts, every get_milliseconds cast in both branches, the chrono_formatter seconds assignment, all system-clock subsecond/one-second casts plus both gmtime(val) calls, and both local-time subsecond casts plus both localtime(val) calls.
8. [B08] Make the production edit now. The harness compiles it after this response; if a second turn supplies one compiler diagnostic, repair that existing patch without redesigning it or dropping any completed migration item.
