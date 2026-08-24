# DMF-C06 instruction: authenticated official terminal behavior

## Contract

The pinned instructions, metadata, reference files, CMake file, Catch dependency, test main, and official Diamond tests must match their SHA-256 values. The complete official suite must compile warning-cleanly, execute, exit zero, and report five passing assertions in five cases.

| Kernel | Pass condition |
| --- | --- |
| C06-A | All nine protected task assets authenticate |
| C06-B | The complete official suite compiles and links under strict C++17 flags |
| C06-C | The executable exits zero and reports all five assertions passing |

C06 is independently necessary even in strict mode. `official` compatibility mode uses C06 alone for acceptance, while the default `strict` mode requires C01-C06.
