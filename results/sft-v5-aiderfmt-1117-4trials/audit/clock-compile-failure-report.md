# Clock Compile-Failure Report: Exact Issues and Diagnostics

This report isolates the compile/build-failure category for the Aider Polyglot `clock` task across SFT-v5 trials a2, a4, a5, and a8. It compares both attempts in every trajectory with the pinned Clock reference, separates primary defects from cascading compiler messages, and records the precise diagnostic that stopped each build.

Across eight attempts there are **six compiler failures, one linker failure, and one compiled-but-test-failing attempt**. All four retries end in compiler failure: a2 and a5 are stopped by the same `-Werror=format-truncation` pattern, a4 contains two independent compile defects, and a8 removes the required `operator!=` declaration while trying to repair an earlier duplicate-definition link error.

## Primary evidence table

| Component or category | Role or failure pattern | Evidence or current status | How to verify | Files, controls, or next action |
| --- | --- | --- | --- | --- |
| Official Exercism problem | Defines what the model was trying to implement | **Verified:** date-independent 24-hour clock; add/subtract minutes; normalized equality; C++ API also requires `at`, string conversion, `plus`, `minus`, `==`, and free `!=` | Read upstream instructions, reference header/implementation, and tests at commit `413b80a...` | Current upstream is semantically equivalent to the evaluator's pinned Clock files |
| Attempt denominator | Separates terminal and all-attempt counts | **Verified:** 4 trajectories x 2 attempts = 8 attempts; 6 compile, 1 link, 1 test failure | Extract `tasks/clock/.aider.chat.history.md` from each trial archive | `trials/{a2,a4,a5,a8}/responses.tar.gz` |
| Terminal compile category | Exact requested category | **Verified:** 4/4 second attempts fail compilation; no Clock repair succeeds | Inspect a2 lines 1491-1501, a4 4287-4308, a5 856-866, and a8 1228-1233/2105-2107 | Counts are mutually exclusive at trajectory level |
| Language-version syntax | Unsupported operator syntax | a2.1 emits C++20 `auto operator<=>(...) = default` under C++17, causing three parser messages from one defect | a2 lines 696-704 | Remove unrequested spaceship syntax |
| Warning-as-error formatting | Fixed buffer cannot be proven safe | a2.2 and a5.2 use `char[6]` with `%02d:%02d`; GCC says output could need 6-14 bytes | a2 1491-1501; a5 856-866 | Use reference stream formatting or compiler-provable bounds |
| Missing standard header | Formatter symbols undeclared | a4.2 uses `std::setw` and `std::setfill` without `<iomanip>`, causing four use-site errors | a4 4287-4305 | Include `<iomanip>` as in reference `example.cpp:2` |
| Broken inequality repair | Wrong operator form and identifier | a4.2 changes free `operator!=` into a member but keeps `lhs`, which is not a member parameter | a4 4307-4308 | Restore the required free operator |
| Header/source drift | Definitions absent from class declaration | a5.1 emits seven errors rooted in missing constructor declarations and missing `_minute` state | a5 383-424 | Synchronize `.h` and `.cpp`; reference header lines 21-25 |
| ODR/linkage | Same symbol defined twice | a8.1 defines free `operator!=` in both header and source | a8 644-645 | Declare once and define once, or use one `inline` header definition |
| Missing overload | Repair deletes public declaration | a8.2 leaves no visible free `operator!=`; the official test expression cannot resolve an overload | a8 1228-1233, 2102-2107 | Preserve declaration while removing only duplicate definition |

## What the official Exercism Clock problem requires

The upstream problem statement is deliberately small: implement a clock without dates, support adding and subtracting minutes, and make clocks representing the same time equal. The exact C++ contract is supplied by the track's reference header and tests, not by the two starter files.

Upstream `main` was inspected at commit [`413b80a9b94089e4588c50500b8553a59c48cda8`](https://github.com/exercism/cpp/commit/413b80a9b94089e4588c50500b8553a59c48cda8). Its Clock files were diffed against the evaluator's pinned Polyglot commit `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f`; the differences are formatting, include order, and `#pragma once` versus an include guard. The API, normalization algorithm, formatter behavior, and all test vectors are semantically unchanged.

| Official requirement | Exact upstream evidence | What success means | Where the SFT runs failed |
| --- | --- | --- | --- |
| Date-independent clock | [Instructions](https://github.com/exercism/cpp/blob/413b80a9b94089e4588c50500b8553a59c48cda8/exercises/practice/clock/.docs/instructions.md) | Store a time-of-day only; discard whole-day overflow | a2 retry contains a latent exact-negative-day normalization defect |
| Factory/API shape | [Reference header](https://github.com/exercism/cpp/blob/413b80a9b94089e4588c50500b8553a59c48cda8/exercises/practice/clock/.meta/example.h) | `date_independent::clock::at(hour, minute=0)`, mutating `plus`/`minus`, implicit string conversion, and `operator==` compile with exact signatures | a5 header/source drift; a4 malformed member `!=`; a8 removes free `!=` |
| Canonical 24-hour normalization | [Reference implementation](https://github.com/exercism/cpp/blob/413b80a9b94089e4588c50500b8553a59c48cda8/exercises/practice/clock/.meta/example.cpp#L36-L50) and [19 construction cases](https://github.com/exercism/cpp/blob/413b80a9b94089e4588c50500b8553a59c48cda8/exercises/practice/clock/clock_test.cpp#L18-L39) | Large positive/negative hours and minutes normalize into `00:00` through `23:59` | a2 retry can map exact negative day multiples to minute 1440; others mostly fail before semantics run |
| Exact `HH:MM` rendering | [Reference formatter](https://github.com/exercism/cpp/blob/413b80a9b94089e4588c50500b8553a59c48cda8/exercises/practice/clock/.meta/example.cpp#L29-L34) | Implicit string conversion emits five characters with two-digit hour and minute | a4 directly returns `8:0`/`10:3`; a2/a5 repairs fail strict compilation; a8 retains unpadded `to_string` |
| Signed minute arithmetic | [16 add/subtract cases](https://github.com/exercism/cpp/blob/413b80a9b94089e4588c50500b8553a59c48cda8/exercises/practice/clock/clock_test.cpp#L49-L66) | `plus` handles zero, positive, negative, cross-midnight, and multi-day deltas; reference API also exposes `minus` | a4 reaches `10:03` numerically but fails formatting; a2/a5/a8 lack direct arithmetic evidence because builds stop |
| Normalized equality/inequality | [15 equality cases](https://github.com/exercism/cpp/blob/413b80a9b94089e4588c50500b8553a59c48cda8/exercises/practice/clock/clock_test.cpp#L81-L215) and [free `operator!=`](https://github.com/exercism/cpp/blob/413b80a9b94089e4588c50500b8553a59c48cda8/exercises/practice/clock/.meta/example.h#L25-L27) | Equivalent normalized clocks compare equal; unequal clocks work through namespace-scope `operator!=` | a4 uses the wrong operator form; a8 duplicates it and then deletes its visible declaration |

The official data contains **50 behavioral cases**: 19 construction/format cases, 16 signed-addition cases, and 15 equality cases. These families overlap—for example, construction cases test both normalization and rendering—so 50 is a test-vector count, not 50 independent requirements.

One verifier nuance matters: current official tests express subtraction by passing negative values to `plus`; they do not directly call `minus`. The reference header and injected evaluation contract still require `minus`, so an exact-API verifier must enforce it separately. The existing Clock overlay does so; there is no missing or contradictory model instruction.

## What the model was doing when it failed

| Trial | Intended Clock work | Progress before failure | Exact reason it did not solve the official problem |
| --- | --- | --- | --- |
| a2 | Complete header-only class with normalization, rendering, and comparisons | Chose a total-minutes representation and initially had a canonical modulo expression | Added unrequested C++20 syntax under C++17; retry replaced good modulo logic with an edge-case-broken formula and used a warning-failing formatter |
| a4 | Implement `.h`/`.cpp`, then repair zero-padding exposed by official tests | First attempt compiled and reached all three test families; equality passed while two rendering assertions failed | Repair knew `setw`/`setfill` were needed but omitted `<iomanip>` and rewrote free inequality as an invalid member |
| a5 | Implement declarations in `clock.h` and behavior in `clock.cpp` | Source contained construction, arithmetic, normalization, rendering, and equality ideas | Header omitted constructors/state; retry fixed the interface but added a formatter rejected by `-Werror` |
| a8 | Implement a header-oriented clock and resolve `operator!=` linkage | Normalization and core methods compiled in attempt 1 | Defined free `operator!=` twice; retry removed its public declaration. Unpadded rendering remained behind the compile gate |

The official comparison makes the diagnosis more precise than “Clock algorithm failure”: **the model understood much of the domain but repeatedly failed to deliver the exact C++17 interface and a warning-clean repair**. Only a4.1 provides direct official semantic evidence, and it isolates zero-padding rather than arithmetic.

## Exact attempt classification

| Attempt | Stage reached | Exact primary issue | Direct diagnostic | Outcome |
| --- | --- | --- | --- | --- |
| a2.1 | Compile tests | C++20 spaceship operator in C++17 | `declaration of ‘operator<=’ as non-function`; expected `;`; unexpected `>` | Compile fail |
| a2.2 | Compile tests | Six-byte `snprintf` buffer triggers truncation analysis | `%02d directive output may be truncated`; output 6-14 bytes into size 6 | Compile fail, terminal |
| a4.1 | Run tests | Missing zero-padding | `"08:00" == "8:0"`; `"10:03" == "10:3"` | Test fail, not compile |
| a4.2 | Compile source | Missing `<iomanip>` and malformed member `operator!=` | `setw/setfill is not a member of std`; `lhs was not declared` | Compile fail, terminal |
| a5.1 | Compile source | Header omits constructors and `_minute` | No matching constructor declarations; `_minute` not declared/member absent | Compile fail |
| a5.2 | Compile source | Same fixed-buffer warning as a2.2 | `%02d directive output may be truncated`; warnings treated as errors | Compile fail, terminal |
| a8.1 | Link executable | Free `operator!=` defined twice | `multiple definition`; `ld returned 1 exit status` | Link fail |
| a8.2 | Compile tests | Repair removes `operator!=` declaration | `no match for operator!=` for two `const clock` operands | Compile fail, terminal |

## Trial a2: unsupported syntax, then warning-unsafe formatting

Attempt 1 submits:

```cpp
auto operator<=>(const clock& rhs) const = default;
```

The C++17 parser reports:

```text
clock.h:57:10: error: declaration of ‘operator<=’ as non-function
clock.h:57:18: error: expected ‘;’ at end of member declaration
clock.h:57:20: error: expected unqualified-id before ‘>’ token
```

These are three messages from **one primary defect**. The prompt requests `operator==` and free `operator!=`; the extra C++20 operator is unnecessary.

Attempt 2 removes it but uses:

```cpp
char buffer[6];
snprintf(buffer, sizeof(buffer), "%02d:%02d", hours, minutes);
```

The terminal diagnostic is:

```text
clock.h:49:43: error: ‘%02d’ directive output may be truncated writing between 2 and 9 bytes into a region of size 6 [-Werror=format-truncation=]
clock.h:49:17: note: ‘snprintf’ output between 6 and 14 bytes into a destination of size 6
cc1plus: all warnings being treated as errors
```

The buffer fits only if the intended value invariant already holds, but GCC cannot prove that bound. The reference avoids the warning through `ostringstream`, `<iomanip>`, `setw(2)`, and `setfill('0')`.

## Trial a4: semantic failure regresses into two compile defects

Attempt 1 compiles and links but returns unpadded values. Official assertions show expected `08:00`, actual `8:0`, and expected `10:03`, actual `10:3`.

The repair uses the right manipulators but omits their defining header:

```text
clock.cpp:31:17: error: ‘setw’ is not a member of ‘std’
clock.cpp:31:33: error: ‘setfill’ is not a member of ‘std’
clock.cpp:31:69: error: ‘setw’ is not a member of ‘std’
clock.cpp:31:85: error: ‘setfill’ is not a member of ‘std’
note: ‘std::setw’ and ‘std::setfill’ are defined in header ‘<iomanip>’
```

It independently changes the required free operator into a member while retaining a nonexistent `lhs` parameter:

```text
clock.cpp:40:14: error: ‘lhs’ was not declared in this scope; did you mean ‘rhs’?
```

Therefore a4 has **two independent terminal defects**: missing `<iomanip>` and an invalid operator/API rewrite. Its context/output exhaustion is an overlapping operational signal, not another compile error.

## Trial a5: header/source drift, then warning-unsafe formatting

Attempt 1 defines constructors and accesses `_minute` in `clock.cpp`, but its header declares neither. GCC emits seven error sites:

```text
clock.cpp:6:14: error: definition of implicitly-declared ‘constexpr date_independent::clock::clock()’
clock.cpp:8:1: error: no declaration matches ‘date_independent::clock::clock(int, int)’
clock.cpp:20:30: error: no matching function for call to ‘date_independent::clock::clock(int&, int&)’
clock.cpp:24:5: error: ‘_minute’ was not declared in this scope
clock.cpp:36:25: error: ‘_minute’ was not declared in this scope
clock.cpp:47:12: error: ‘_minute’ was not declared in this scope
clock.cpp:47:27: error: ‘const class date_independent::clock’ has no member named ‘_minute’
```

The seven messages reduce to **two primary defects**: missing constructor declarations and missing object state. The reference declares a private two-argument constructor and state in `example.h:21-25`; it needs no default constructor because `at()` uses that private constructor.

Attempt 2 fixes the declarations but introduces a2's fixed-buffer pattern:

```text
clock.cpp:42:39: error: ‘%02d’ directive output may be truncated writing between 2 and 9 bytes into a region of size 6 [-Werror=format-truncation=]
clock.cpp:42:13: note: ‘snprintf’ output between 6 and 14 bytes into a destination of size 6
cc1plus: all warnings being treated as errors
```

The repair responds to the first diagnostics but fails to compile its new formatter with the evaluator's strict flags.

## Trial a8: duplicate definition repaired by deleting the API

Attempt 1 compiles but fails at link time because free `operator!=` exists in both files:

```text
multiple definition of `date_independent::operator!=(date_independent::clock const&, date_independent::clock const&)'
clock.cpp.o: clock.cpp:55; clock_test.cpp.o: clock.h:55 first defined here
collect2: error: ld returned 1 exit status
```

This is an ODR/link failure, not a compiler failure, but it supplies the feedback for attempt 2.

The repair removes the duplicate and the header declaration required by callers. Compilation then reports:

```text
clock_test.cpp:213:28: error: no match for ‘operator!=’
operand types are ‘const date_independent::clock’ and ‘const date_independent::clock’
catch.hpp:2325:96: error: no match for ‘operator!=’
```

The long list of standard-library overload candidates is cascading lookup output, not separate Clock errors. Correct repair preserves a namespace-scope header declaration and exactly one definition, or uses the reference's one `inline` header definition.

## Primary defects versus cascading diagnostics

| Attempt | Raw error sites | Independent defects | Explanation |
| --- | ---: | ---: | --- |
| a2.1 | 3 | 1 | One unsupported token sequence causes three parser errors |
| a2.2 | 1 fatal warning site | 1 | Range notes are not separate failures |
| a4.2 | 5 | 2 | Four manipulator errors share one missing header; undefined `lhs` is separate |
| a5.1 | 7 | 2 | Missing constructor declarations and state cascade across methods |
| a5.2 | 1 fatal warning site | 1 | Same formatter defect as a2.2 |
| a8.2 | 2 main sites plus lookup notes | 1 | Test and Catch helper expose the same missing overload |

Raw GCC messages must not be summed as model failures. There are four trajectories, each with one terminal outcome, even when one candidate contains several independent defects.

## Reference-solution delta

| Reference requirement | Source-of-truth location | Candidate delta | Trials |
| --- | --- | --- | --- |
| C++17 equality surface | `example.h:19,28-31` | Adds unsupported `<=>`, changes free `!=` into invalid member, duplicates it, or deletes it | a2, a4, a8 |
| `<iomanip>` | `example.cpp:2` | Uses `setw`/`setfill` without header | a4 |
| Stream zero-padding | `example.cpp:32-37` | Uses unpadded `to_string` or warning-prone fixed buffer | a2, a4, a5; a8 latent |
| Declared construction/state | `example.h:21-25` | Source defines constructors and accesses state absent from class | a5 |
| One ODR-safe free `operator!=` | `example.h:28-31` | Defines twice, then removes public visibility | a8 |

## Directly verified facts

- The exact diagnostics above occur in the archived Clock chats at the cited extracted-chat lines.
- Terminal failures are: a2 format truncation; a4 missing `<iomanip>` plus undefined `lhs`; a5 format truncation; a8 missing `operator!=`.
- Across both attempts, a8.1 is the only link failure and a4.1 is the only attempt that reaches and fails tests.
- The reference declares its private constructor/state in the header, includes `<iomanip>`, uses stream formatting, and defines free `operator!=` once as `inline`.
- C++17 strict warnings include `-Werror`, so a2/a5 warning diagnostics are terminal compile failures.

## Inferences and boundaries

- Primary-defect counts are causal groupings inferred from diagnostic relationships; raw messages are direct evidence.
- The a2/a5 buffers could hold a correctly normalized five-character time plus NUL. No runtime overflow is claimed; the observed failure is that strict static analysis cannot prove safety.
- a4's context exhaustion may have reduced repair quality, but the log does not prove causation.
- a8 retains an unpadded formatter after retry. That is latent semantic debt, not its observed terminal compile error.
- No model rerun was performed, so training-effect claims remain unverified.

## Recommended compile-repair slice

1. C++17-only repair: remove unrequested C++20 syntax without rewriting working methods.
2. Header/source synchronization: derive a declaration checklist before emitting both files.
3. Diagnostic grouping: teach that multiple messages may descend from one missing declaration/header.
4. Warning-clean formatting: compile with exact `-Wall -Wextra -Wpedantic -Werror` flags.
5. ODR-preserving repair: convert duplication to declaration-plus-one-definition without deleting the API.
6. Gate each repair: exact signatures -> strict compile -> link -> focused formatting -> official suite.

## Implemented category verifier package

The follow-on implementation is in `Reward_GRPO/clock_verifiers_v2/`. It contains separate `Instruction/` and `Implementation/` reports for nine categories, executable C01-C08 source verifiers, the diagnostic-only C09 repair-transition verifier, an aggregate runner, and a controlled-mutant validation harness. The pinned reference passed 24/24 kernels; all eight targeted mutants were rejected by both their intended policy and mandatory C08, with zero terminal survivors.

See `Reward_GRPO/clock_verifiers_v2/README.md` for the frozen reward contract and `Reward_GRPO/clock_verifiers_v2/validation/VALIDATION_REPORT.md` for the final matrix and remaining production boundaries.

## Reproduction map

Each archive contains `tasks/clock/.aider.chat.history.md`:

```text
results/sft-v5-aiderfmt-1117-4trials/trials/<trial>/responses.tar.gz
```

Relevant extracted-chat ranges:

- a2: 696-704 and 1491-1501.
- a4: 3706-3724 for attempt 1; 4287-4308 for terminal compilation.
- a5: 383-424 and 856-866.
- a8: 644-645 for linking; 1228-1233 and 2102-2107 for terminal compilation.

The injected contract is `reproduction/aider_fixed26_contract_overlay.py:199-218`. The benchmark source of truth is Polyglot commit `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f`, exercise `cpp/exercises/practice/clock/.meta/example.h` and `.meta/example.cpp`.

## Conclusion

Clock's terminal compile failures are exact-interface and build-discipline failures, not timeouts: two warning-unsafe formatters, one repair with a missing include plus malformed operator body, and one repair that deletes a required overload. The next concrete check is to train and replay these four diagnostic-conditioned repairs under the strict compiler before changing broader Clock semantics.
