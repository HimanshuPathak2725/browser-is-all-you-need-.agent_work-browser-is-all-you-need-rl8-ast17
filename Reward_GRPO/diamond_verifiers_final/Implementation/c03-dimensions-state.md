# DMF-C03 implementation report

`verifier_03_dimensions_state.py` checks all 26 input sizes and every row width, then exercises saved, repeated, and interleaved calls. This targets the dominant iter-19 failure family: compile-clean implementations whose row count, width, or retained state is wrong.

The probes use only the public API and independent side-length arithmetic. Three of the four observed iter-19 final candidates fail C03; the fourth has correct dimensions but is rejected by the exact geometry policies.
