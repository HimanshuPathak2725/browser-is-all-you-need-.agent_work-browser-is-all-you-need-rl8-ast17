# Full-v5 GRPO fixed-26 completion audit

## Scope and evidence

This audit covers the terminal evaluation of GRPO iteration 56:

- Run: `glm47-aider-full-v5-sftv5-grpo-3ep-fixed26-20260724T164100Z`
- Adapter SHA-256: `1dbed2ffcb99e69fef187e24c229699f67dcb171a39b54b722fdf6d6cba9617f`
- Aider commit: `5dc9490bb35f9729ef2c95d00a19ccd30c26339c`
- Polyglot commit: `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f`
- Sampling: temperature `0.7`, top-p `1.0`, two attempts per task

The downloaded evaluation tree is under:

`artifacts/glm47-aider-full-v5-sftv5-grpo-3ep-fixed26-20260724T164100Z/glm47-aider-full-v5-sftv5-grpo-3ep-fixed26-20260724T164100Z/`

For every task, that tree contains:

- `.aider.chat.history.md`: the initial completion, compiler/test feedback, and repair completion;
- `.aider.results.json`: terminal outcomes and token/error counters;
- the final generated `.cpp`/`.h` files;
- the test source used by the benchmark; and
- `.meta/example.cpp` and `.meta/example.h`: the benchmark's reference implementation.

The `.meta/example.*` files were checked against the pinned Polyglot commit. They are the source of truth used for the ground-truth summaries below. The run receipt reports 26 unique terminal tasks and 52/52 expected attempts.

## Exact aggregate result

| Measure | Result |
| --- | ---: |
| pass@1 | 0/26 (0.0%) |
| Passed within two attempts | 5/26 (19.2%) |
| Failed after both attempts | 21/26 (80.8%) |
| Well-formed task outputs | 26/26 |
| Malformed responses | 0 |
| Error-output records | 4 |
| Context-exhaustion records | 4 |
| Test timeouts | 0 |

### Mutually exclusive outcome accounting

| Stage | Compilation/link failure | Compiled but tests failed | Passed | Total |
| --- | ---: | ---: | ---: | ---: |
| Attempt 1 | 25 | 1 | 0 | 26 |
| Attempt 2 / terminal | 18 | 3 | 5 | 26 |

Therefore the defensible terminal statement is:

> Eighteen of the 21 tasks that failed after both attempts (85.7%), or 18/26 tasks overall (69.2%), ended in a C++ compilation or link failure. Three terminal failures compiled and were partially correct under the benchmark tests. Five tasks passed only after compiler/test feedback.

It is **not** correct to describe these as 18 malformed patches. The Aider output parser recorded 26/26 well-formed tasks and zero malformed responses. Most failures were valid whole-file edits that violated the existing C++ public API, type, or linkage contract. One terminal task, `zebra-puzzle`, contains a direct C++ syntax error.

### Overlapping secondary flags

These are not additional mutually exclusive tasks:

- `bank-account`, `binary-search-tree`, `clock`, and `zebra-puzzle` recorded context exhaustion and an error output. Each still has concrete terminal compiler/test evidence, so context exhaustion is secondary to the terminal outcome below.
- `spiral-matrix` attempted to edit `spiral_matrix_test.cpp`, a file not supplied for editing. Aider's transcript records the out-of-scope edit attempt. The preserved terminal test file is byte-identical to the pinned benchmark test, so the benchmark safeguard prevented that edit from changing the oracle.
- No task timed out, and no task has a malformed response.

## Per-task completion and reference analysis

The “attempt 1” and “attempt 2” columns describe what the benchmark actually compiled or tested, not an inference from prose. “Ground truth” summarizes the pinned `.meta/example.*` implementation.

| # | Task | Ground-truth contract and solution | Attempt 1 | Attempt 2 / terminal result | Primary classification |
| ---: | --- | --- | --- | --- | --- |
| 1 | `all-your-base` | Expose `all_your_base::convert(unsigned, const vector<unsigned>&, unsigned)`; validate bases and digits, fold the source digits into a value, then emit target-base digits by division/remainder. | Did not expose the expected `convert` symbol. | Added `convert`, but used `vector<int>` and `int`; tests pass `vector<unsigned int>`, so compilation stopped on reference binding. No tests ran. | Compile: public signature/type mismatch |
| 2 | `allergies` | Keep an `allergy_test` object around a bitmask; `is_allergic_to(string const&)` checks one bit and `get_allergies()` returns the selected allergen names. | Implemented namespace functions rather than the required `allergy_test` type, so every test reference to the class failed to compile. | Added the class, but `allergy_test::is_allergic_to` called `is_allergic_to(item, score_)` unqualified. Member-name hiding selected the one-argument member set, producing “no matching function” at `allergies.cpp:50`. | Compile: member-call/name-resolution error |
| 3 | `bank-account` | Implement `open`, `close`, `balance`, `deposit`, and `withdraw` around integer state and a mutex; reject operations on closed accounts, duplicate open/close, negative amounts, and overdrafts. | Replaced the required API with a constructor-centric `double` account; tests could not find `open()` or the expected `balance()` contract. | Compiled and passed 9/17 tests. All eight failures were missing exception checks: deposits/withdrawals on closed accounts, invalid close/open, overdraft, and negative deposit/withdraw. A context-exhausted reflection was also recorded. | Partial hidden-test correctness: 9/17; secondary context exhaustion |
| 4 | `binary-search-tree` | Implement templated `binary_tree<T>`, insertion, `data()/left()/right()` accessors, and an in-order iterator. | The required `binary_tree` template was absent, causing a cascade beginning at the test helper's type declaration. | Declared fields named `data`, `left`, and `right` and methods with the same names. These conflicting declarations and invalid accessor calls prevented compilation. The final reflection also exhausted context. | Compile: conflicting data/member API; secondary context exhaustion |
| 5 | `circular-buffer` | Provide a header-visible `circular_buffer<T>` ring with `read`, `write`, `overwrite`, and `clear`, throwing on empty/full operations as required. | Used class name `CircularBuffer` rather than `circular_buffer<T>`, so test declarations failed. | Corrected the class name, but put template definitions in `.cpp` and instantiated only `int`, `float`, and `double`. String-buffer tests produced undefined references at link time. `count_` was also left uninitialized, but tests never reached runtime. | Link failure: unavailable template instantiations |
| 6 | `clock` | Expose lowercase `date_independent::clock`, `clock::at`, mutating `plus`/`minus`, string conversion, and equality; normalize all minutes modulo 24 hours. | Exposed uppercase `Clock` and `subtract`/`toString`, not the supplied API. | Retained uppercase `Clock`; tests still could not resolve `date_independent::clock`. A reflection call exhausted context. | Compile: class/method naming contract; secondary context exhaustion |
| 7 | `complex-numbers` | Use private real/imaginary storage with callable `real()`/`imag()`, arithmetic and scalar operators, `abs`, `conj`, and complex exponential. | Public data fields named `real` and `imag` collided with the tests' expected callable accessors. | Kept those fields and also declared methods named `real()` and `imag()`, creating direct declaration conflicts; the constructor was defined both inline and out of line as well. | Compile: member-name and redefinition errors |
| 8 | `crypto-square` | Expose `crypto_square::cipher` and normalize alphanumeric lowercase text into square/rectangle segments and ciphertext. | Omitted the expected `crypto_square::cipher` class. | Reconstructed the tested class/API and passed all 8/8 assertions. | Pass after repair |
| 9 | `diamond` | Expose the free function `diamond::rows(char)` and generate the symmetric letter rows with the correct outer/inner spaces. | Implemented a `Diamond` class instead of the namespace function. | Retained the class-only API; `diamond::rows` was still absent. No tests ran. | Compile: wrong API shape |
| 10 | `dnd-character` | `ability()` rolls four dice and drops the lowest; `modifier()` uses floor division; the default `Character` constructor fills six abilities and a `hitpoints` member. | Did not provide the required `Character` type. | Added `Character`, but omitted its constructor and `hitpoints` field, so the tests failed at `character.hitpoints`. The standalone `hitpoints(character)` helper did not satisfy the contract. | Compile: missing public member/constructor |
| 11 | `gigasecond` | `gigasecond::advance(const boost::posix_time::ptime&)` returns the input timestamp plus one billion seconds. | The expected `advance` function was missing. | Implemented `advance(std::tm)` instead of Boost `ptime`; test arguments could not convert to `tm`. | Compile: wrong time type/signature |
| 12 | `grade-school` | Store `map<int, vector<string>>`; add uniquely, return alphabetically sorted students for a grade, and expose the roster with the exact expected types. | Used `map<int, set<string>>` in the public return type, so test comparison with `map<int, vector<string>>` did not compile. | Restored the expected API/types and passed all 8/8 assertions. | Pass after repair |
| 13 | `kindergarten-garden` | Use the exact `Plants` enum and return `array<Plants, 4>` from `plants(string_view, string_view)` by indexing the two diagram rows for the named student. | Did not expose the expected `Plants` type. | Added `Plants`, but returned `vector<Plants>` and accepted `string`; tests expected `array<Plants,4>` and `string_view`, so comparison failed to compile. | Compile: container/signature mismatch |
| 14 | `knapsack` | Expose `maximum_value(int, const vector<Item>&)` and solve the 0/1 knapsack maximum-value problem, normally with capacity dynamic programming. | Omitted the expected `maximum_value` function. | Reconstructed the API and dynamic program; passed all 7/7 assertions. | Pass after repair |
| 15 | `linked-list` | Implement the templated doubly linked `List<T>` with `push`, `pop`, `shift`, `unshift`, `count`, and `erase`, preserving ownership and empty-list errors. | Declared `Node` members without `Node<T>` template arguments, causing missing-field cascades in `List<T>`. | Corrected the template declarations and behavior; passed all 42 assertions in 19 test cases. | Pass after repair |
| 16 | `meetup` | Construct `meetup::scheduler` with Boost Gregorian month/year types and return `boost::gregorian::date` from all teenth/first/second/third/fourth/last weekday methods. | Did not define the expected `scheduler` type. | Added `scheduler`, but returned integer day numbers instead of Boost dates and used a weekday calculation unrelated to the real calendar. Compilation stopped on `boost::gregorian::date == int`. | Compile: wrong return type and calendar contract |
| 17 | `parallel-letter-frequency` | Expose `frequency(vector<string_view> const&) -> unordered_map<char, size_t>` and aggregate case-insensitive letter counts across inputs. | Accepted `vector<string>` rather than `vector<string_view>`. | Switched to a generic template returning `map<char,int>`, but left its definition in `.cpp`; the `string_view` instantiation was unavailable and the linker reported undefined references. | Link failure: unavailable template instantiation; return type also wrong |
| 18 | `perfect-numbers` | Use `enum class classification { deficient, perfect, abundant }`; sum proper divisors, reject non-positive inputs, and classify the number. | Used a differently named `Classification` type/API. | Changed to an unscoped enum with capitalized members `Perfect/Abundant/Deficient`; tests require the exact lowercase scoped enumerators, so compilation failed. | Compile: enum type/member naming contract |
| 19 | `phone-number` | Clean NANP punctuation, accept a leading country code `1`, reject bad length/letters, and enforce area/exchange leading digits 2–9; expose `number`, `area_code`, and string formatting. | Exposed `Phone_Number` instead of `phone_number::phone_number`. | Compiled but passed only 3/18 tests. It rejected valid punctuated/11-digit forms before normalization and failed to reject invalid area/exchange prefixes; many expected domain errors were missing or replaced by the wrong length error. | Partial hidden-test correctness: 3/18 |
| 20 | `queen-attack` | `chess_board` validates two in-bounds, distinct queens; exposes positions, board rendering, and row/column/diagonal attack detection. | Did not expose the expected `chess_board` type. | Compiled and passed 10/14 test cases (11/15 assertions). The four failures were all missing constructor validation for negative or out-of-range rows/columns. | Partial hidden-test correctness: 10/14 cases |
| 21 | `robot-name` | Lowercase `robot` owns a mutable unique `AA000`-style name generated at construction; `name()` returns a const reference and `reset()` assigns a new name. | Exposed uppercase `Robot`, so the expected type was absent. | Restored lowercase `robot`, but made `name()` const while lazily assigning to non-mutable `name_`; compilation failed on assignment through a const object. It also lacked the required constructor initialization. | Compile: const-correctness/constructor contract |
| 22 | `space-age` | Expose lowercase `space_age::space_age`, preserve integer seconds, and divide Earth years by each planet's orbital ratio. | Exposed uppercase `SpaceAge`. | Retained uppercase `SpaceAge`, so tests still could not name `space_age::space_age`. | Compile: class naming contract |
| 23 | `spiral-matrix` | Expose free function `spiral_matrix::spiral_matrix(uint32_t) -> vector<vector<uint32_t>>`; fill clockwise while rotating at boundaries or occupied cells. | Implemented a class/namespace variant rather than the expected namespace function. | Retained namespace `SpiralMatrix` and class-based API, so the pinned tests could not resolve namespace `spiral_matrix`. The completion also attempted to edit `spiral_matrix_test.cpp`; the preserved test was restored to the pinned oracle. | Compile: wrong namespace/API; secondary out-of-scope test edit |
| 24 | `sublist` | Return exact scoped enum members `equal`, `sublist`, `superlist`, or `unequal` after contiguous subsequence comparison. | Did not provide the required `List_comparison` type. | Added the enum but capitalized every member (`Equal`, `Sublist`, and so on); the lowercase test references failed to compile. | Compile: enum member naming contract |
| 25 | `yacht` | Score all named categories; four-of-a-kind scores exactly four copies of the face even when all five dice match. | Compiled and passed 28/29 assertions. For five threes in “four of a kind,” it returned 15 instead of the required 12. | Used the precise test feedback to correct the edge case; passed all 29/29 assertions. | Pass after semantic repair |
| 26 | `zebra-puzzle` | Expose `Solution solve()` and solve the 15-house constraints, typically by permutations/backtracking; return the nationalities that drink water and own the zebra. | The expected `solve` symbol was absent. This attempt also recorded context exhaustion. | Defined helper functions inside `solve()`, which C++ forbids, then referenced the unavailable nested helper. Compiler errors begin “a function-definition is not allowed here.” The transcript also records a summarizer failure. | Compile: C++ syntax; secondary context/error output |

## Category conclusions

### Compilation

- Attempt 1: 25/26 did not compile; only `yacht` reached the tests.
- Terminal attempt: 18/26 did not compile or link.
- The dominant repeated pattern is failure to preserve the supplied public C++ contract: class/namespace case, exact enum members, container types, Boost types, and template visibility.
- Two terminal failures are specifically link failures (`circular-buffer`, `parallel-letter-frequency`).
- One terminal failure is a direct C++ syntax failure (`zebra-puzzle`).

### Wrong files

- There is one confirmed out-of-scope edit attempt: `spiral-matrix` emitted `spiral_matrix_test.cpp` and accepted Aider's prompt to add it to the chat.
- The terminal preserved test file matches the pinned benchmark file, so this did not alter the oracle.
- The other 25 transcripts only applied edits to the supplied `.cpp`/`.h` filenames.

### Hidden tests and partial correctness

- Three terminal tasks compiled but failed tests: `bank-account` (9/17), `phone-number` (3/18), and `queen-attack` (10/14 test cases).
- `yacht` was already near-correct on attempt 1 (28/29) and became a full pass after feedback.
- For the 18 terminal compile/link failures, hidden-test correctness is unknown because the executable never ran. Plausible-looking reasoning or algorithms in those completions must not be counted as partial correctness.

### Syntax and formatting

- Aider output formatting: 26/26 well formed, zero malformed responses, and aggregate `syntax_errors: 0` in the result metadata.
- C++ compiler syntax: `zebra-puzzle` has a real language-level syntax error. These two notions of “syntax” are different.

### Context exhaustion and truncation

- Four tasks recorded context exhaustion/error output: `bank-account`, `binary-search-tree`, `clock`, and `zebra-puzzle`.
- The schema does not contain a standalone “completion truncated” field for this run. The transcripts show empty/exhausted reflection calls, but every task still produced code that the terminal benchmark compiled or tested. It is therefore safer to report four context-exhaustion events, not four conclusively truncated terminal completions.

## What this audit can and cannot attribute

This evidence is sufficient to attribute the immediate evaluation outcomes: why each attempt compiled, failed tests, or passed. It supports “18/21 terminal failures were compilation/link failures” and refutes “the failures were mostly malformed response formatting.”

The evaluation artifacts alone do not prove that a particular GRPO reward component caused those failures. Causal attribution to training requires a matched checkpoint comparison and the training reward/rollout ledger. The separate full-v5 training archive can support that larger comparison, but it should remain distinct from this per-completion outcome audit.
