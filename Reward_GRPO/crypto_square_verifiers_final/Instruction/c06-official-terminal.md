# CSF-C06 instruction: authenticated official terminal behavior

## Contract

The pinned instructions, metadata, reference files, CMake file, Catch dependency, test main, and official Crypto Square tests must match their SHA-256 values. The complete official suite must compile warning-cleanly, execute, exit zero, and report eight passing assertions in eight cases.

| Kernel | Pass condition |
| --- | --- |
| C06-A | All nine protected task assets authenticate |
| C06-B | The complete official suite compiles and links under strict C++17 flags |
| C06-C | The executable exits zero and reports all eight assertions passing |

C06 is independently necessary in strict mode. `official` compatibility mode uses C06 alone, while the default `strict` mode requires C01-C06.
