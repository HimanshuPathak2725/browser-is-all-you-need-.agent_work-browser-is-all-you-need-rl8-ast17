# CLF-C03 implementation report

`verifier_03_integration_odr.py` combines v2’s repeated-include and multi-TU probes with original E05’s factory/observer independence checks. The multi-TU executable calls both string conversion and free inequality from a helper translation unit, catching duplicate and missing symbols under normal linker rules.

Source-text heuristics are excluded. A legal out-of-line or inline implementation passes if compiler/linker behavior and runtime state isolation are correct.
