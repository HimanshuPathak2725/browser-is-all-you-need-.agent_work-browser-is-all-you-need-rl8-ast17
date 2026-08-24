# KGF-C02 implementation report

`verifier_02_exact_api_integration.py` uses compile-time enum and function-pointer assertions, followed by repeated-include and multi-translation-unit probes. This distinguishes the required `string_view` API and `char`-backed enum from interfaces that remain callable through implicit conversion.

The integration probes catch missing guards and non-inline header definitions that the single-translation-unit official build accepts. A legal named include guard is retained as a positive control, preventing enforcement of `#pragma once` specifically.
