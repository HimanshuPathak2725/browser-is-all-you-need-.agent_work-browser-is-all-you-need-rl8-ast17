# Implementing DNF-C04

The old verifier and official suite checked only output range. On the common corpus they accepted constant-10, uniform `[3,18]`, three-dice, and alternating-extreme implementations. Iter-19 trial 2 also initially summed all four dice and produced 19.

The final policy first provides a cheap support signal, then independently enumerates all 1,296 legal four-die outcomes and compares a 100,000-call candidate histogram. The total-variation and mean thresholds are deliberately wider than ordinary sampling noise; eight independent valid implementations passed, including `std::rand`, `std::mt19937`, `thread_local`, per-call seeded, source-defined, and inline-header forms.
