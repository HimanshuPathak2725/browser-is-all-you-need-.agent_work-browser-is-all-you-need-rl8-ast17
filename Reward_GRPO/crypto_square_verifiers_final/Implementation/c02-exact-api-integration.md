# CSF-C02 implementation report

`verifier_02_exact_api_integration.py` uses typed member pointers to distinguish exact const method signatures from merely callable overloads. It separately compiles a repeated-include probe and a multi-translation-unit caller that invokes the complete public surface on the empty boundary.

Keeping C02-C on empty input makes it an integration signal rather than a duplicate layout oracle. Validation catches non-const methods, incorrect return types, missing include guards, and non-inline header definitions without requiring a specific private representation.
