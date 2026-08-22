# C06 implementation report: formatting and warnings

`verifier_06_formatting_warning_cleanliness.py` combines strict independent compilation with exact public rendering probes and repeated const conversion. It accepts any implementation strategy that is warning-clean and produces canonical output.

The reference passed 3/3. The unpadded formatter mutant passed C01-C05 but failed C06, C07, and terminal C08, demonstrating useful localization. The observed a2/a5 fixed-buffer warning also fails C06-A before runtime.

| Kernel | Implementation | Evidence |
| --- | --- | --- |
| C06-A | Strict `clock.cpp` compilation | Warning/error log |
| C06-B | Checks `00:00`, `08:03`, `23:59`, and `04:43` | Exact marker after assertions |
| C06-C | Repeated const conversion, length five, colon at index two | Link/run receipt |

C06 and semantic/terminal policies overlap on rendered values by design. Do not count their failures independently.
