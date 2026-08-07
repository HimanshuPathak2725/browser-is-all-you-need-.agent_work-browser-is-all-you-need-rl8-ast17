# R5 fmtlib failure summary

## Evidence identity

- Run: `synthmem-v3-v1std-50ep-fmtlib-v2-20260807T043648Z`
- Task: `fmtlib-fmt-large-time-point-overflow-v2`
- Candidate patch SHA-256: `8077084f29499ee53c79420e192de7a94150bddfd14ac2d57b12aa02c453b9a7`
- Complete failed-build log SHA-256: `16ca9153f93f7d6f4e4fdaad687404a079e8f66ab982c8f0d615da374c63464b`
- Changed production file: `include/fmt/chrono.h`
- Failed command: `cmake --build build-public-pr-eval --target chrono-test --parallel 2`
- Build return code: `2`

## Candidate changes

The candidate attempted to:

- route local-time conversion through a new `to_time_t` helper;
- add an arithmetic-type trait and a generic `fmt_duration_cast` implementation;
- use the new cast helper in fractional-second, millisecond, formatter, and time-point paths; and
- keep the production change within `include/fmt/chrono.h`.

The patch also accidentally removed structural code from the
`get_milliseconds` region, including the closing conditional directive,
function closure, and integral `format_duration_value` overload. The fallback
branch was left with an incomplete statement and no return path.

## First root compiler error

The first diagnostic in the complete compiler log is:

```text
include/fmt/chrono.h:8: error: unterminated #ifndef
8 | #ifndef FMT_CHRONO_H_
```

This is not a defect in the header guard itself. The candidate removed the
`#endif` belonging to the inner `#if FMT_SAFE_DURATION_CAST` block near
`get_milliseconds`. Consequently, the final `#endif` closed the wrong
conditional and the outer `FMT_CHRONO_H_` guard remained unterminated.

## Independent primary compilation error

The new helpers were declared in `fmt::v10`, before reopening
`namespace detail`, but their consumers called them as members of
`fmt::v10::detail`:

```text
include/fmt/chrono.h:574:18: error: 'fmt_duration_cast' is not a member of 'fmt::v10::detail'
note: 'fmt::v10::fmt_duration_cast' declared here
```

The helper definitions and every qualified call therefore disagreed about
lexical scope. The `to_time_t` helper had the same placement problem.

## Downstream cascades

After the preprocessor and namespace structure became invalid, parsing of
later standard-library and test declarations cascaded. Errors involving
GoogleTest declarations and
`type_is_unformattable_for<tm, char>` are downstream symptoms. They do not
identify the first root failure: the malformed conditional structure and
helper namespace mismatch occur earlier.

## Missing or incomplete mechanisms

| Mechanism | Required correction |
| --- | --- |
| Arithmetic-category dispatch | Treat integral-to-integral and floating-to-floating representations as compatible categories, even when the concrete types differ. The candidate trait recognized only identical concrete types. |
| Helper namespace and placement | Place `fmt_duration_cast` and `to_time_t` inside `namespace detail`, after the safe-duration-cast machinery and before their consumers. |
| C++11 helper syntax | Avoid deduced function return types that require a later language standard; retain warning-clean C++11 syntax. |
| Generic `gmtime` overload | Add `template <typename Duration>` to the system-clock time-point overload, accept `time_point<system_clock, Duration>`, and call `detail::to_time_t` directly. |
| Fractional-second conversions | Route both the whole-second subtraction and the subsecond-precision conversion through the unified helper. |
| Obsolete helper removal | Remove the old `fmt_safe_duration_cast` path after all consumers use the unified helper. |
| Millisecond conversion paths | Preserve the complete function structure and route both safe and fallback paths through valid checked conversions without deleting return paths. |
| Chrono formatter conversion | Use the unified helper from its actual namespace while preserving the original constructor and surrounding declarations. |
| System-clock root correction | Pass `val` directly to the templated `gmtime` overload instead of narrowing with `time_point_cast<std::chrono::seconds>`. |
| Local-time root correction | Pass `val` directly to `localtime` instead of narrowing with `time_point_cast<std::chrono::seconds>`. |

## Required repair order

1. Restore the removed `#endif`, braces, return path, and integral formatter overload.
2. Move the new helpers into `namespace detail` and make all qualifications consistent.
3. Replace the identical-type trait with arithmetic-category dispatch.
4. Implement the generic `gmtime` overload and direct time-point conversion.
5. Complete every fractional, millisecond, formatter, system-clock, and local-time conversion site.
6. Compile the C++11 chrono target before interpreting any later test or formatter diagnostics.

The executable build must succeed before the independent runtime probe can
provide meaningful behavioral evidence.
