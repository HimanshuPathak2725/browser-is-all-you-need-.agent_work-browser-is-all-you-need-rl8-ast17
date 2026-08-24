# DMF-C06 policy: authenticated official terminal behavior

## Contract

The pinned instructions, metadata, reference files, CMake file, Catch dependency, test main, and official Diamond tests must match their SHA-256 values. The complete official suite must compile warning-cleanly, execute, exit zero, and report five passing assertions in five cases.

| Kernel | Pass condition |
| --- | --- |
| C06-A | All nine protected task assets authenticate |
| C06-B | The complete official suite compiles and links under strict C++17 flags |
| C06-C | The executable exits zero and reports all five assertions passing |

C06 is independently necessary even in strict mode. `official` compatibility mode uses C06 alone for acceptance, while the default `strict` mode requires C01-C06.

## Implementation rationale

`verifier_06_official_terminal.py` preserves the authenticated official terminal boundary while sharing the final package's common receipt and preflight implementation. Nine protected assets are hash-pinned before the five-case suite is compiled directly with strict GCC flags and executed.

An official-macro sabotage control passes C01-C05 and fails only C06, proving that selected property probes cannot replace the protected terminal suite. Altered assets or missing tools return `INVALID`; candidate compile, assertion, or runtime errors return `FAIL`.
