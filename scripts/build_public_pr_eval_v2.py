#!/usr/bin/env python3
"""Build the immutable three-task public-PR diagnostic evaluation contract."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import textwrap
from pathlib import Path
from typing import Any

from glm47_posttraining.public_pr_eval.fmt_verified_contract import upgrade_thinking_row
from glm47_posttraining.public_pr_eval.validator import (
    BASELINE_REPAIR_INSTRUCTION_IDS,
    BASELINE_REPAIR_PROMPT_PROFILE,
    COMPACT_REPAIR_INSTRUCTION_IDS,
    COMPACT_REPAIR_PROMPT_PROFILE,
    FINAL_CLEANUP_REPAIR_PARENT_PROMPT_SHA256,
    FINAL_CLEANUP_REPAIR_PROMPT_PROFILE,
    FINAL_CLEANUP_REPAIR_SUFFIX,
    PRIORITIZED_REPAIR_INSTRUCTION_IDS,
    PRIORITIZED_REPAIR_PARENT_PROMPT_SHA256,
    PRIORITIZED_REPAIR_PROMPT_PROFILE,
    CLASSIFICATION,
    COMPILER_FEEDBACK_DISCLOSURE,
    COMPILER_FEEDBACK_MODE,
    EXACT_FEEDBACK,
    FIRST_DEMO_BASELINE_PRESERVED_MECHANISMS,
    FIRST_DEMO_BASELINE_PROMPT_SHA256,
    REQUIRED_WORKFLOW_INSTRUCTION_IDS,
    RESPONSE_PROTOCOL,
    SCHEMA_VERSION,
    canonical_json,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
IMAGE = (
    "radixark/miles:latest-cu12@"
    "sha256:efc8027fc47aaa9687dc4f1046093ed4e2f9789e52a932fcefb7031402aeff37"
)

LEGACY_FMT_PR_SOLUTION_CHECKLIST = [
    {
        "id": "fmt-duration-cast-helper",
        "change": "Add detail::fmt_duration_cast<>",
        "purpose": "centralize duration conversion and route same-category casts through safe_duration_cast when enabled",
        "path": "include/fmt/chrono.h",
        "required_substrings": [
            "fmt_duration_cast",
            "safe_duration_cast::safe_duration_cast<To>",
            'FMT_THROW(format_error("cannot format duration"))',
        ],
        "forbidden_substrings": [],
    },
    {
        "id": "same-arithmetic-dispatch",
        "change": "Add same arithmetic type dispatch for safe casts",
        "purpose": "avoid invoking safe_duration_cast for unsupported mixed integer/floating conversions",
        "path": "include/fmt/chrono.h",
        "required_substrings": [
            "is_same_arithmetic_type",
            "std::is_integral<Rep1>::value",
            "std::is_floating_point<Rep1>::value",
        ],
        "forbidden_substrings": [],
    },
    {
        "id": "safe-cast-placement",
        "change": "Place fmt_duration_cast after safe_duration_cast machinery",
        "purpose": "ensure fmt_duration_cast can call safe_duration_cast::safe_duration_cast<To> without forward-reference or overload visibility problems",
        "path": "include/fmt/chrono.h",
        "required_substrings": [
            "safe_duration_cast::safe_duration_cast<To>",
            "fmt_duration_cast",
        ],
        "ordered_substrings": [
            "namespace safe_duration_cast",
            "fmt_duration_cast",
        ],
        "forbidden_substrings": [],
    },
    {
        "id": "to-time-t-helper",
        "change": "Add detail::to_time_t()",
        "purpose": "convert system_clock time points to time_t without first narrowing to system_clock::duration",
        "path": "include/fmt/chrono.h",
        "required_substrings": [
            "std::time_t to_time_t",
            "time_point.time_since_epoch()",
            "fmt_duration_cast<std::chrono::duration<std::time_t>>",
        ],
        "forbidden_substrings": [],
    },
    {
        "id": "templated-gmtime",
        "change": "Templatize gmtime() over Duration",
        "purpose": "accept time_point<system_clock, Duration> directly instead of only native precision",
        "path": "include/fmt/chrono.h",
        "required_substrings": [
            "template <typename Duration>",
            "std::chrono::time_point<std::chrono::system_clock, Duration> time_point",
            "return gmtime(detail::to_time_t(time_point));",
        ],
        "forbidden_substrings": [],
    },
    {
        "id": "localtime-to-time-t",
        "change": "Fix localtime(local_time<Duration>)",
        "purpose": "preserve local-time formatting without native system_clock narrowing",
        "path": "include/fmt/chrono.h",
        "required_substrings": [
            "detail::to_time_t(std::chrono::current_zone()->to_sys(time))",
        ],
        "forbidden_substrings": [
            "std::chrono::system_clock::to_time_t(\n      std::chrono::current_zone()->to_sys(time))",
        ],
    },
    {
        "id": "fractional-seconds-casts",
        "change": "Use fmt_duration_cast in write_fractional_seconds()",
        "purpose": "preserve fractional-second arithmetic while keeping checked conversion behavior",
        "path": "include/fmt/chrono.h",
        "required_substrings": [
            "d - fmt_duration_cast<std::chrono::seconds>(d)",
            "fmt_duration_cast<subsecond_precision>(fractional).count()",
        ],
        "forbidden_substrings": [],
    },
    {
        "id": "remove-old-safe-helper",
        "change": "Delete fmt_safe_duration_cast<>",
        "purpose": "replace the old macro-only helper with the unified fmt_duration_cast wrapper",
        "path": "include/fmt/chrono.h",
        "required_substrings": [],
        "forbidden_substrings": ["fmt_safe_duration_cast"],
    },
    {
        "id": "milliseconds-casts",
        "change": "Use fmt_duration_cast in get_milliseconds()",
        "purpose": "keep whole-second and millisecond remainder conversions checked consistently",
        "path": "include/fmt/chrono.h",
        "required_substrings": [
            "fmt_duration_cast<CommonSecondsType>(d)",
            "fmt_duration_cast<std::chrono::seconds>(d_as_common)",
            "fmt_duration_cast<std::chrono::milliseconds>(d - s)",
        ],
        "forbidden_substrings": [],
    },
    {
        "id": "chrono-formatter-cast",
        "change": "Use fmt_duration_cast in chrono_formatter::on_duration_value()",
        "purpose": "collapse the safe/raw duration cast branch into one checked conversion path",
        "path": "include/fmt/chrono.h",
        "required_substrings": [
            "s = fmt_duration_cast<seconds>(std::chrono::duration<rep, Period>(val));",
        ],
        "forbidden_substrings": [],
    },
    {
        "id": "time-point-root-fix",
        "change": "Remove time_point_cast<seconds> before gmtime()",
        "purpose": "fix the original large-date overflow by passing val directly to templated gmtime()",
        "path": "include/fmt/chrono.h",
        "required_substrings": [
            "formatter<std::tm, Char>::do_format(gmtime(val), ctx, &subsecs)",
            "formatter<std::tm, Char>::format(gmtime(val), ctx)",
        ],
        "forbidden_substrings": [
            "gmtime(std::chrono::time_point_cast<std::chrono::seconds>(val))",
        ],
    },
    {
        "id": "local-time-root-fix",
        "change": "Remove time_point_cast<seconds> before localtime()",
        "purpose": "mirror the system_clock fix for local_time formatting",
        "path": "include/fmt/chrono.h",
        "required_substrings": [
            "formatter<std::tm, Char>::do_format(localtime(val), ctx, &subsecs)",
            "formatter<std::tm, Char>::format(localtime(val), ctx)",
        ],
        "forbidden_substrings": [
            "localtime(std::chrono::time_point_cast<std::chrono::seconds>(val))",
        ],
    },
]


FMT_PR_SOLUTION_CHECKLIST = [
    {**copy.deepcopy(item), "verifier_id": item["id"]}
    for item in LEGACY_FMT_PR_SOLUTION_CHECKLIST
]


def prompt(value: str) -> str:
    return textwrap.dedent(value).strip() + "\n"


REPOSITORY_EDIT_WORKFLOW = (
    (
        "W01",
        "Confirm the objective, reproduction, required behaviors, invariants, editable file, and forbidden paths before editing.",
    ),
    (
        "W02",
        "Inspect the current editable file and the narrow surrounding implementation; do not infer the code from the task description or prior attempts.",
    ),
    (
        "W03",
        "Inspect the current diff or worktree state first so an earlier partial edit is never mistaken for the evaluator baseline.",
    ),
    (
        "W04",
        "Use focused exact-symbol searches to locate every declaration, definition, overload, specialization, and call site relevant to the change.",
    ),
    (
        "W05",
        "Build a symbol inventory before editing: record each function's signature, namespace, callers, callees, side effects, and error behavior.",
    ),
    (
        "W06",
        "Check every relevant header include, include guard, forward declaration, macro dependency, and declaration-order requirement.",
    ),
    (
        "W07",
        "Map namespace opening and closing boundaries exactly; verify the intended namespace at both the helper definition and every call site.",
    ),
    (
        "W08",
        "Map class and struct boundaries plus public, protected, and private access before changing any member or API.",
    ),
    (
        "W09",
        "Inventory relevant local, global, member, static, and constexpr variables; verify scope, lifetime, initialization, mutability, and ownership.",
    ),
    (
        "W10",
        "Inventory template parameters, aliases, traits, SFINAE conditions, specializations, and the complete overload set before adding an overload.",
    ),
    (
        "W11",
        "Trace every relevant preprocessor definition and branch, including where each symbol exists when a feature macro is enabled or disabled.",
    ),
    (
        "W12",
        "Confirm the repository's required language standard and use only syntax and library facilities available in that standard.",
    ),
    (
        "W13",
        "Read each relevant function body to determine its actual behavior; never guess functionality from a name, comment, or compiler-highlighted line.",
    ),
    (
        "W14",
        "Trace values and control flow from input through conversions, callbacks, fallbacks, state mutations, errors, and final output.",
    ),
    (
        "W15",
        "Create a requirement-to-code map so every requested behavior has one identified implementation point and one validation check.",
    ),
    (
        "W16",
        "Identify the smallest root cause before editing; treat later compiler errors as possible cascades until the first diagnostic is resolved.",
    ),
    (
        "W17",
        "Reuse an existing helper only after confirming its exact signature, semantics, namespace, visibility, supported types, and macro availability.",
    ),
    (
        "W18",
        "Preserve deliberate portability, feature-detection, ADL, and fallback functions unless the requirement and call graph prove they must change.",
    ),
    (
        "W19",
        "Preserve public and private API signatures, access levels, names, and observable behavior unless the task explicitly authorizes a change.",
    ),
    (
        "W20",
        "Verify every changed function's return type, parameter types, cv/ref qualifiers, constness, noexcept status, and all return paths.",
    ),
    (
        "W21",
        "Declare every template parameter before use and confirm dependent names use the required typename, template, and qualification syntax.",
    ),
    (
        "W22",
        "Qualify each symbol from its actual lexical scope; do not add or remove namespace qualification by visual guesswork.",
    ),
    (
        "W23",
        "Check that overload resolution is unambiguous and that constraints are mutually correct for integral, floating, mixed, and platform-specific types.",
    ),
    (
        "W24",
        "Audit conversions for signed and unsigned range, narrowing, overflow, underflow, precision, NaN, infinity, signed zero, and boundary values as applicable.",
    ),
    (
        "W25",
        "Check all affected macro and platform configurations conceptually and compile more than one branch when the repository provides such targets.",
    ),
    (
        "W26",
        "Do not add a new include, helper, allocation, global state, or persistent variable unless it is necessary and its lifetime and ABI impact are verified.",
    ),
    (
        "W27",
        "Do not add unnecessary function calls, repeated conversions, duplicate scans, duplicate helpers, or work inside hot paths; reuse proven results locally.",
    ),
    (
        "W28",
        "Modify only the exact allowlisted production file; never edit tests, generated output, build files, baselines, or unrelated headers.",
    ),
    (
        "W29",
        "Keep the patch minimal and coherent: no unrelated cleanup, renaming, reformatting, comment churn, or speculative refactoring.",
    ),
    (
        "W30",
        "If an edit block fails or applies partially, re-read the current file, distinguish applied from unapplied blocks, and never replay successful edits.",
    ),
    (
        "W31",
        "After one coherent edit, run the smallest warning-clean compile or target that instantiates the changed declarations before making further changes.",
    ),
    (
        "W32",
        "When compilation fails, read the first root diagnostic and its notes, verify the implicated definition and scope, then fix that cause before cascades.",
    ),
    (
        "W33",
        "Inspect the final diff line by line for syntax, braces, namespace closure, preprocessor balance, declaration order, duplicate definitions, and accidental deletions.",
    ),
    (
        "W34",
        "Repeat focused searches for every required replacement, every forbidden stale pattern, and every affected call site after the edit.",
    ),
    (
        "W35",
        "Run the relevant upstream target and supplied probe or sanitizer checks after the focused compile passes; do not substitute visual similarity for execution.",
    ),
    (
        "W36",
        "Do not claim success while any compiler, test, sanitizer, scope, or checklist failure remains; if execution is unavailable, leave the result explicitly unverified.",
    ),
    (
        "W37",
        "Satisfy the workspace-edit response protocol with an actual production edit; explanatory prose, hypothetical patches, and test-only changes are not completion.",
    ),
    (
        "W38",
        "Stop once the mapped requirements and validations pass; avoid extra calls and further code changes that do not close a demonstrated gap.",
    ),
)


FMT_IMPLEMENTATION_AUDIT = (
    (
        "F01",
        "Define the unified duration-cast helper in `namespace detail` and route checked same-category casts through the existing safe-cast machinery.",
    ),
    (
        "F02",
        "Use integral/integral or floating/floating category dispatch; keep mixed-category conversion on the standard duration cast path without ambiguity.",
    ),
    (
        "F03",
        "Place the helper only after safe-cast definitions are visible and before its callers; do not move, replace, or retype the existing time fallback functions.",
    ),
    (
        "F04",
        "Define `detail::to_time_t` with a declared `Duration` template parameter and direct epoch-duration conversion, without native clock-duration narrowing.",
    ),
    (
        "F05",
        "Declare the system-clock `gmtime` overload as a `template <typename Duration>` and call the helper through the namespace where it is actually defined.",
    ),
    (
        "F06",
        "Route the guarded local-time overload through the same safe time conversion while preserving timezone behavior and feature guards.",
    ),
    (
        "F07",
        "Replace both fractional-second conversion sites: whole-second subtraction and subsecond-precision conversion.",
    ),
    (
        "F08",
        "Remove the obsolete macro-only safe-cast wrapper only after every caller has moved to the unified helper.",
    ),
    (
        "F09",
        "Update all `get_milliseconds` conversions in both safe and fallback branches while preserving negative-duration remainder behavior.",
    ),
    (
        "F10",
        "Use one unified seconds conversion in `chrono_formatter` without changing representation, sign handling, or formatter structure.",
    ),
    (
        "F11",
        "In the system-clock formatter, preserve fractional and no-fractional paths but pass `val` directly to the templated calendar conversion.",
    ),
    (
        "F12",
        "Mirror the direct-call and subsecond changes in the local-time formatter without changing its no-subseconds dispatch.",
    ),
)


CATCH2_IMPLEMENTATION_AUDIT = (
    (
        "C01",
        "Locate the producer, consumer, and reset points for every saved assertion field before changing the lifecycle.",
    ),
    (
        "C02",
        "Ensure the current assertion consumes its own result disposition and reaction before any reset can alter its outcome.",
    ),
    (
        "C03",
        "Reset all transient classification fields on every completion path that leaves saved assertion information active.",
    ),
    (
        "C04",
        "Verify true and false `CHECKED_ELSE` paths followed by an uncaught exception reach the same failing terminal state.",
    ),
    (
        "C05",
        "Preserve incomplete-handler cleanup, counters, sections, expected-failure policy, and reporter callback ordering.",
    ),
    (
        "C06",
        "Keep the reset local to existing lifecycle code; do not add reporter-specific conditions, output fabrication, or public API changes.",
    ),
)


SIMDJSON_IMPLEMENTATION_AUDIT = (
    (
        "S01",
        "Locate every zero-producing floating conversion path, including zero significands and exponent underflow below the subnormal range.",
    ),
    (
        "S02",
        "Construct zero with the already parsed sign at the conversion point; do not rewrite source text or patch the sign after parsing.",
    ),
    (
        "S03",
        "Apply the correction to all shared generic paths so DOM, On-Demand, runtime SIMD implementations, and portable fallback remain consistent.",
    ),
    (
        "S04",
        "Verify negative forms yield negative zero and corresponding positive forms remain positive zero.",
    ),
    (
        "S05",
        "Preserve nonzero subnormals, normal finite values, integers, rounding, malformed-input rejection, and overflow errors.",
    ),
    (
        "S06",
        "Do not add platform-specific bit manipulation, public API changes, parser-state changes, or special cases for the listed literals.",
    ),
)


def numbered_section(heading: str, instructions: tuple[tuple[str, str], ...]) -> str:
    return (
        heading
        + "\n\n"
        + "\n".join(
            f"{index}. [{instruction_id}] {instruction}"
            for index, (instruction_id, instruction) in enumerate(instructions, 1)
        )
    )


def repository_edit_workflow() -> str:
    ids = tuple(item[0] for item in REPOSITORY_EDIT_WORKFLOW)
    if ids != REQUIRED_WORKFLOW_INSTRUCTION_IDS:
        raise ValueError(
            "repository-edit workflow IDs do not match the validator contract"
        )
    return numbered_section(
        "# Mandatory repository-edit workflow", REPOSITORY_EDIT_WORKFLOW
    )


def task_implementation_audit(instructions: tuple[tuple[str, str], ...]) -> str:
    return numbered_section("# Task-specific implementation self-audit", instructions)


def append_prompt_sections(base: str, *sections: str) -> str:
    return (
        base.rstrip()
        + "\n\n"
        + "\n\n".join(section.strip() for section in sections)
        + "\n"
    )


def command(name: str, argv: list[str], timeout: int) -> dict[str, Any]:
    return {"name": name, "argv": argv, "timeout_seconds": timeout}


def environment(dependency_identities: dict[str, str]) -> dict[str, Any]:
    return {
        "image": IMAGE,
        "platform": "linux/amd64",
        "toolchain": {
            "cc": "gcc-13",
            "cxx": "g++-13",
            "cmake": "3.27.9",
            "generator": "Unix Makefiles",
        },
        "locale": "C.UTF-8",
        "timezone": "UTC",
        "provisioning_network": "image_build_only",
        "runtime_network": "disabled",
        "dependencies": "prefetched_and_digest_bound_in_image",
        "dependency_identities": dependency_identities,
        "resource_limits": {
            "cpu_cores": 8,
            "memory_mib": 32768,
            "disk_mib": 24576,
            "command_timeout_seconds": 1800,
        },
    }


def common_row(
    *,
    task_id: str,
    user_prompt: str,
    repository: dict[str, str],
    editable_file: str,
    hidden_validation: dict[str, Any],
    dependency_identities: dict[str, str],
    reference_patch_sha256: str,
    provenance: dict[str, str],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": task_id,
        "classification": CLASSIFICATION,
        "capability_tags": hidden_validation.pop("capability_tags"),
        "model_input": {
            "messages": [{"role": "user", "content": user_prompt}],
            "network_access": "disabled",
            "response_protocol": RESPONSE_PROTOCOL,
        },
        "repository": {
            **repository,
            "reference_visibility": "evaluator_only",
        },
        "scope": {
            "mode": "exact_allowlist",
            "editable_files": [editable_file],
            "protected_policy": "all_repository_paths_except_editable_files",
            "reject_unlisted_changes": True,
            "require_production_change": True,
            "reject_symlink_or_submodule_changes": True,
        },
        "environment": environment(dependency_identities),
        "output_contract": {
            "kind": "workspace_edit",
            "edit_format": "whole",
            "candidate_diff_source": "git_diff_against_evaluator_baseline",
            "malformed_response": "attempt_failure",
            "final_answer_text_is_not_a_substitute_for_workspace_changes": True,
        },
        "hidden_validation": hidden_validation,
        "run_policy": {
            "attempts": 2,
            "pass_at_1": "initial repository state after the first model response",
            "pass_at_2": "repository state after one exact redacted-feedback turn",
            "attempt_2_feedback": EXACT_FEEDBACK,
            "feedback_disclosure": "status_only_no_private_details",
            "temperature": 0.7,
            "top_p": 1.0,
            "seeds": [1701],
            "max_completion_tokens": 32768,
            "thinking_mode": "disabled",
        },
        "integrity": {
            "model_prompt_sha256": hashlib.sha256(
                user_prompt.encode("utf-8")
            ).hexdigest(),
            "reference_patch_sha256": reference_patch_sha256,
        },
        "provenance": {
            **provenance,
            "contamination_risk": "public_patch_possible_pretraining_overlap",
            "training_eligibility": "forbidden",
            "permitted_use": "diagnostic_base_or_checkpoint_evaluation_only",
        },
    }


def tasks() -> list[dict[str, Any]]:
    fmt_prompt = prompt(
        """
        # Objective

        Correct chrono formatting for `std::chrono::time_point<std::chrono::system_clock,
        Duration>` when `Duration` can represent calendar instants outside the range of the
        clock's native duration. The implementation must solve the general conversion problem;
        it must not special-case the example date or hardcode formatted output.

        # Failure reproduction

        On this 64-bit Linux evaluator, the following C++11 value must format as
        `3000-01-01` with the format string `{:%Y-%m-%d}`:

        ```cpp
        using time_point = std::chrono::time_point<std::chrono::system_clock,
                                                   std::chrono::milliseconds>;
        time_point value{std::chrono::seconds(32503680000LL)};
        ```

        The current implementation narrows through the native `system_clock::duration` before
        producing calendar fields. That intermediate conversion can overflow even when the
        source duration and the platform calendar conversion can represent the requested date.

        # Required behavior

        - Format the reproduction value as exactly `3000-01-01`.
        - Support other large positive and negative epochs without a native-duration overflow.
        - Preserve ordinary dates, negative epochs, and fractional seconds.
        - Preserve integral, floating-point, mixed-representation, and coarse-duration behavior.
        - Preserve local-time formatting when the platform and configured C++ library expose it.
        - When `FMT_SAFE_DURATION_CAST` is enabled, a checked same-category duration conversion
          that is not representable must throw `fmt::format_error`; it must never wrap.
        - Keep existing overflow rejection and error messages compatible unless the corrected
          checked-conversion path requires the documented format error.

        # Compatibility and invariants

        Preserve all public APIs and the repository's C++11 compatibility. Keep conversions
        generic over duration representation and period. Do not introduce undefined signed
        overflow, implementation-specific integer-width assumptions, global state, or a
        platform-only shortcut. Existing thread safety, locale behavior, and formatting of
        normal chrono values must remain unchanged.

        # Editable scope

        Modify only `include/fmt/chrono.h`. Do not modify tests, CMake files, documentation,
        generated files, vendored dependencies, or any other repository path. Do not modify
        public API signatures. Do not hardcode the supplied epoch, year, or expected text.

        # Validation expectations

        The evaluator performs a warning-clean C++11 compile, the upstream chrono test target,
        independent large-date and negative-epoch probes, and undefined-behavior sanitizer
        execution. It also checks the checked-cast exception path and verifies that every path
        outside the one editable production header is byte-identical to the evaluator baseline.

        # Response contract

        Work directly in the supplied repository using Aider whole-file editing. Make the
        smallest coherent production change that satisfies the complete contract. Do not return
        prose in place of an edit, and do not create tests, patches, helper files, or build files.
        """
    )
    catch_prompt = prompt(
        """
        # Objective

        Correct the transient assertion-state lifecycle after `CHECKED_ELSE` processing. A later
        uncaught exception must be classified from its own assertion context, not from a stale
        result disposition left by the preceding checked assertion. Solve the lifecycle defect;
        do not special-case reporter names, test names, or exception text.

        # Failure reproduction

        A test case executes either `CHECKED_ELSE(true) {}` or `CHECKED_ELSE(false) {}` and then
        throws an uncaught `std::runtime_error`. In the broken state, the saved assertion result
        disposition can survive the checked assertion. The later exception can consequently be
        omitted or treated as successful, and console-style and XML-style reporters can disagree
        about the terminal test result.

        # Required behavior

        - An uncaught exception after `CHECKED_ELSE(true)` must be reported and fail normally.
        - The same must hold after `CHECKED_ELSE(false)`.
        - Console, XML, and the existing reporter families must agree on the terminal status.
        - Reset every transient assertion field that can affect classification, including result
          disposition, on every completion path that leaves saved assertion information active.
        - The current assertion's reaction must consume its own disposition before that state is
          reset; an early reset that changes the current assertion is incorrect.
        - Preserve incomplete assertion-handler cleanup, expected-failure, may-fail, skip,
          section, and reporter semantics.

        # Compatibility and invariants

        Preserve the public API, supported C++ standard, exception translation, event ordering,
        assertion accounting, and reporter callback ordering. Keep the reset operation local to
        the assertion lifecycle. Do not hide exceptions, manufacture reporter output, or solve
        the reproduction by changing test-case success policy.

        # Editable scope

        Modify only `src/catch2/internal/catch_run_context.cpp`. Do not modify tests, approved
        reporter baselines, public headers, generated files, CMake files, or unrelated sources.
        Do not modify public API signatures. Do not hardcode the reproduction cases, reporter
        names, exception message, or expected output.

        # Validation expectations

        The evaluator builds the warning-clean `SelfTest` target and runs the full upstream test
        suite with the evaluator-only regression overlay. A separately compiled probe checks both
        boolean branches under console and XML reporters with a fixed framework random seed. The
        evaluator also rejects resets placed before reaction consumption and verifies the exact
        repository-wide editable-file allowlist.

        # Response contract

        Work directly in the supplied repository using Aider whole-file editing. Make one
        coherent production fix. Do not answer with explanatory prose instead of editing the
        file, and do not create or modify tests, baselines, patches, documentation, or build files.
        """
    )
    simd_prompt = prompt(
        """
        # Objective

        Preserve IEEE 754 signed zero when a syntactically negative JSON number evaluates to zero
        during floating-point parsing. The correction must cover every relevant zero-producing
        conversion path; it must not hardcode the example strings or apply a post-parse string
        rewrite.

        # Failure reproduction

        Through the DOM parser, sufficiently small negative inputs such as `-1e-999`, `-0e-999`,
        and `-0.0e-999` currently produce positive zero. The parsed `double` compares equal to
        zero, but `std::signbit` is false. Each negative form must instead produce negative zero.
        The equivalent On-Demand cases are part of the compatibility contract even where the
        pinned base already handles them correctly.

        # Required behavior

        - DOM parsing of negative exponent underflow must return zero with `std::signbit` set.
        - On-Demand parsing must preserve the same negative sign.
        - A negative zero significand must remain negative when the exponent also underflows.
        - Corresponding positive inputs must remain positive zero.
        - Cover both a zero significand and exponent underflow below the subnormal range.
        - Preserve nonzero subnormal values, ordinary finite floating-point values, integers, and
          existing overflow rejection.
        - Apply consistently across supported runtime SIMD implementations and portable fallback
          code that shares the generic number parser.

        # Compatibility and invariants

        Preserve the public API, error codes, parser state transitions, supported C++ standard,
        exception/no-exception configurations, and integer fast paths. Do not weaken malformed
        JSON validation, accept infinities, change rounding of representable values, or add a
        platform-specific sign-bit manipulation that bypasses normal `double` construction.

        # Editable scope

        Modify only `include/simdjson/generic/numberparsing.h`. Do not modify tests, generated
        amalgamations, single-header output, CMake files, benchmarks, documentation, dependencies,
        or unrelated code. Do not modify public API signatures. Do not hardcode the listed JSON
        literals or their expected bit patterns.

        # Validation expectations

        The evaluator uses CMake 3.27.9 with all dependencies prefetched before network isolation.
        It builds and runs the complete upstream test suite plus an independent warning-clean C++17
        DOM/On-Demand signed-zero probe covering negative and positive forms. It also checks normal
        numbers, overflow rejection, subnormal behavior, and the exact repository-wide file
        allowlist.

        # Response contract

        Work directly in the supplied repository using Aider whole-file editing. Implement the
        smallest general production correction. Do not return prose instead of editing the file,
        and do not create tests, patches, generated files, documentation, or build configuration.
        """
    )

    workflow = repository_edit_workflow()
    fmt_prompt = append_prompt_sections(
        fmt_prompt, workflow, task_implementation_audit(FMT_IMPLEMENTATION_AUDIT)
    )
    catch_prompt = append_prompt_sections(
        catch_prompt, workflow, task_implementation_audit(CATCH2_IMPLEMENTATION_AUDIT)
    )
    simd_prompt = append_prompt_sections(
        simd_prompt, workflow, task_implementation_audit(SIMDJSON_IMPLEMENTATION_AUDIT)
    )

    fmt_hidden = {
        "capability_tags": ["chrono", "checked-conversion", "signed-overflow", "c++11"],
        "overlay": {
            "source": "reference_commit_diff",
            "include_paths": ["test/chrono-test.cc"],
            "exclude_paths": ["include/fmt/chrono.h"],
            "patch_sha256": "2d2a302ddd61d9a50ab9597399012bd161e07547c151607fdd57a01bdca822fb",
            "file_manifest_sha256": "9f31b01ebd2e0b49b6658611a844dc8b16dbcc00dc962d3c73f9be99c4ea1778",
        },
        "independent_probe": {
            "path": "configs/public_pr_eval/private_probes/fmt_large_time_point_probe.cpp",
            "sha256": "35b51f0395f3ad4587e33d3a4d3c4ebdc9476d00bbda186b089d20021f413fb6",
        },
        "provision_commands": [
            command(
                "configure",
                [
                    "cmake",
                    "-S",
                    ".",
                    "-B",
                    "build-public-pr-eval",
                    "-DFMT_TEST=ON",
                    "-DFMT_DOC=OFF",
                    "-DCMAKE_BUILD_TYPE=Debug",
                    "-DFETCHCONTENT_BASE_DIR=.public-pr-eval-deps",
                ],
                900,
            ),
        ],
        "build_commands": [
            command(
                "configure-offline",
                [
                    "cmake",
                    "-S",
                    ".",
                    "-B",
                    "build-public-pr-eval",
                    "-DFMT_TEST=ON",
                    "-DFMT_DOC=OFF",
                    "-DCMAKE_BUILD_TYPE=Debug",
                    "-DFETCHCONTENT_BASE_DIR=.public-pr-eval-deps",
                    "-DFETCHCONTENT_FULLY_DISCONNECTED=ON",
                ],
                900,
            ),
            command(
                "build-chrono",
                [
                    "cmake",
                    "--build",
                    "build-public-pr-eval",
                    "--target",
                    "chrono-test",
                    "--parallel",
                    "2",
                ],
                1800,
            ),
            command(
                "test-chrono",
                [
                    "ctest",
                    "--test-dir",
                    "build-public-pr-eval",
                    "-R",
                    "^chrono-test$",
                    "--output-on-failure",
                ],
                1800,
            ),
        ],
        "probe_commands": [
            command(
                "compile-probe",
                [
                    "g++-13",
                    "-std=c++11",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-fsanitize=undefined",
                    "-fno-sanitize-recover=undefined",
                    "-Iinclude",
                    "{private_probe}",
                    "-o",
                    "{private_probe_binary}",
                ],
                900,
            ),
            command("run-probe", ["{private_probe_binary}"], 300),
        ],
        "required_behaviors": [
            "year-3000 millisecond time point formats correctly",
            "large integral durations avoid native-clock narrowing",
            "checked unrepresentable same-category conversion throws format_error",
            "ordinary and negative epochs remain correct",
            "fractional and mixed representation behavior is preserved",
            "C++11 compile is warning-clean and UBSan-clean",
            "only the editable production header changes",
        ],
        "base_oracle": "must_fail",
        "reference_oracle": "must_pass",
        "plausible_wrong_oracle": "must_fail",
        "plausible_wrong_mutation": "reference_solution_with_native_system_clock_narrowing_restored",
        "plausible_wrong_mutation_spec": {
            "path": "include/fmt/chrono.h",
            "old": "  return gmtime(detail::to_time_t(time_point));\n",
            "new": "  return gmtime(std::chrono::system_clock::to_time_t(\n      std::chrono::time_point_cast<std::chrono::system_clock::duration>(\n          time_point)));\n",
            "expected_replacements": 1,
        },
        "pass_condition": "all commands and behaviors pass and exact allowlist holds",
    }
    catch_hidden = {
        "capability_tags": [
            "state-lifecycle",
            "exception-reporting",
            "reporter-consistency",
        ],
        "overlay": {
            "source": "reference_commit_diff",
            "include_paths": ["tests"],
            "exclude_paths": ["src/catch2/internal/catch_run_context.cpp"],
            "patch_sha256": "fcc04a6e3356a4bf6602ee02ce37ce1cff9a701c33abb6be3668dabc9cd2e799",
            "file_manifest_sha256": "f9826e11722511661a584f3486a808b49a5342481b8d811debcfe61ff8b0523c",
        },
        "independent_probe": {
            "path": "configs/public_pr_eval/private_probes/catch2_checked_else_probe.cpp",
            "sha256": "00849c2e9bbc47123c31fe33abdd643b10ef11f9b2597214f3f5cd31a399e0a3",
        },
        "provision_commands": [
            command(
                "configure",
                [
                    "cmake",
                    "-S",
                    ".",
                    "-B",
                    "build-public-pr-eval",
                    "-DCATCH_DEVELOPMENT_BUILD=ON",
                    "-DCMAKE_BUILD_TYPE=Release",
                    "-DFETCHCONTENT_BASE_DIR=.public-pr-eval-deps",
                ],
                900,
            ),
        ],
        "build_commands": [
            command(
                "configure-offline",
                [
                    "cmake",
                    "-S",
                    ".",
                    "-B",
                    "build-public-pr-eval",
                    "-DCATCH_DEVELOPMENT_BUILD=ON",
                    "-DCMAKE_BUILD_TYPE=Release",
                    "-DFETCHCONTENT_BASE_DIR=.public-pr-eval-deps",
                    "-DFETCHCONTENT_FULLY_DISCONNECTED=ON",
                ],
                900,
            ),
            command(
                "build-selftest",
                [
                    "cmake",
                    "--build",
                    "build-public-pr-eval",
                    "--target",
                    "SelfTest",
                    "--parallel",
                    "2",
                ],
                1800,
            ),
            command(
                "test-all",
                ["ctest", "--test-dir", "build-public-pr-eval", "--output-on-failure"],
                1800,
            ),
        ],
        "probe_commands": [
            command(
                "compile-probe",
                [
                    "g++-13",
                    "-std=c++14",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-Isrc",
                    "-Ibuild-public-pr-eval/generated-includes",
                    "{private_probe}",
                    "build-public-pr-eval/src/libCatch2Main.a",
                    "build-public-pr-eval/src/libCatch2.a",
                    "-pthread",
                    "-o",
                    "{private_probe_binary}",
                ],
                900,
            ),
            command(
                "probe-console",
                ["{private_probe_binary}", "--rng-seed", "1701", "-r", "console"],
                300,
            ),
            command(
                "probe-xml",
                ["{private_probe_binary}", "--rng-seed", "1701", "-r", "xml"],
                300,
            ),
        ],
        "required_behaviors": [
            "exception after CHECKED_ELSE true fails normally",
            "exception after CHECKED_ELSE false fails normally",
            "console and XML reporters agree",
            "result disposition is not retained",
            "current reaction consumes disposition before reset",
            "expected-failure may-fail and skip semantics remain intact",
            "only the editable production source changes",
        ],
        "base_oracle": "must_fail",
        "reference_oracle": "must_pass",
        "plausible_wrong_oracle": "must_fail",
        "plausible_wrong_mutation": "reference_solution_without_result_disposition_reset",
        "plausible_wrong_mutation_spec": {
            "path": "src/catch2/internal/catch_run_context.cpp",
            "old": "        m_lastAssertionInfo.resultDisposition = ResultDisposition::Normal;\n",
            "new": "",
            "expected_replacements": 1,
        },
        "pass_condition": "all commands and behaviors pass and exact allowlist holds",
    }
    simd_hidden = {
        "capability_tags": ["ieee754", "signed-zero", "underflow", "parser"],
        "overlay": {
            "source": "reference_commit_diff",
            "include_paths": [
                "tests/dom/basictests.cpp",
                "tests/ondemand/ondemand_number_tests.cpp",
            ],
            "exclude_paths": ["include/simdjson/generic/numberparsing.h"],
            "patch_sha256": "5e3eb228faa55219561d0780f0ad3b8186739194f2da5356ebade8836af7b7b6",
            "file_manifest_sha256": "7bee206ca9e8f9123789c9490f72ac0912a81f4f44b067ea3bf9e27e7b87f9fa",
        },
        "independent_probe": {
            "path": "configs/public_pr_eval/private_probes/simdjson_signed_zero_probe.cpp",
            "sha256": "155b85b2bf4c13d1398a9f833a7dac8c5c9c54ab7717346209936c709fa62d0f",
        },
        "provision_commands": [
            command(
                "configure-and-prefetch",
                [
                    "cmake",
                    "-S",
                    ".",
                    "-B",
                    "build-public-pr-eval",
                    "-DSIMDJSON_DEVELOPER_MODE=ON",
                    "-DCMAKE_BUILD_TYPE=Debug",
                    "-DFETCHCONTENT_BASE_DIR=.public-pr-eval-deps",
                ],
                1200,
            ),
        ],
        "build_commands": [
            command(
                "configure-offline",
                [
                    "cmake",
                    "-S",
                    ".",
                    "-B",
                    "build-public-pr-eval",
                    "-DSIMDJSON_DEVELOPER_MODE=ON",
                    "-DCMAKE_BUILD_TYPE=Debug",
                    "-DFETCHCONTENT_BASE_DIR=.public-pr-eval-deps",
                    "-DFETCHCONTENT_FULLY_DISCONNECTED=ON",
                ],
                1200,
            ),
            command(
                "build-all",
                ["cmake", "--build", "build-public-pr-eval", "--parallel", "2"],
                1800,
            ),
            command(
                "test-all",
                ["ctest", "--test-dir", "build-public-pr-eval", "--output-on-failure"],
                1800,
            ),
        ],
        "probe_commands": [
            command(
                "compile-probe",
                [
                    "g++-13",
                    "-std=c++17",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-Iinclude",
                    "{private_probe}",
                    "build-public-pr-eval/libsimdjson.a",
                    "-pthread",
                    "-o",
                    "{private_probe_binary}",
                ],
                900,
            ),
            command("run-probe", ["{private_probe_binary}"], 300),
        ],
        "required_behaviors": [
            "DOM negative exponent underflow preserves signbit",
            "On-Demand negative exponent underflow preserves signbit",
            "negative zero significand remains negative",
            "positive underflow remains positive zero",
            "ordinary finite integer overflow and subnormal parsing do not regress",
            "supported runtime implementations remain consistent",
            "only the editable production header changes",
        ],
        "base_oracle": "must_fail",
        "reference_oracle": "must_pass",
        "plausible_wrong_oracle": "must_fail",
        "plausible_wrong_mutation": "reference_solution_with_compute_float_zero_sign_fix_removed",
        "plausible_wrong_mutation_spec": {
            "path": "include/simdjson/generic/numberparsing.h",
            "old": "    d = negative ? -0.0 : 0.0;\n",
            "new": "    d = 0.0;\n",
            "expected_replacements": 2,
        },
        "pass_condition": "all commands and behaviors pass and exact allowlist holds",
    }

    rows = [
        common_row(
            task_id="fmtlib-fmt-large-time-point-overflow-v2",
            user_prompt=fmt_prompt,
            repository={
                "url": "https://github.com/fmtlib/fmt.git",
                "base_commit": "ccc9ab7bf9c5aab0071708a0f65e3019bd96b8fe",
                "reference_commit": "7f8d4191157025813f5fd520cb68738b3ee0fe69",
            },
            editable_file="include/fmt/chrono.h",
            hidden_validation=fmt_hidden,
            dependency_identities={"source_dependencies": "repository_tree_only"},
            reference_patch_sha256="73e0580e401763b2b1a8f396b245d7de4a20ae8726ca96e6a3d75e7aca53238e",
            provenance={
                "upstream_pr_url": "https://github.com/fmtlib/fmt/pull/3727",
                "upstream_issue_url": "https://github.com/fmtlib/fmt/issues/3725",
                "license": "MIT",
            },
        ),
        common_row(
            task_id="catch2-reset-assertion-disposition-v2",
            user_prompt=catch_prompt,
            repository={
                "url": "https://github.com/catchorg/Catch2.git",
                "base_commit": "b593be21160766291bfef7ccb8b1471a4a64abd9",
                "reference_commit": "cd60a0301cf8dd8da076166ad865f21325bc24fe",
            },
            editable_file="src/catch2/internal/catch_run_context.cpp",
            hidden_validation=catch_hidden,
            dependency_identities={"source_dependencies": "repository_tree_only"},
            reference_patch_sha256="a8a59d65c79a1f53a220d0f2a57abf96c588aa4907ff15acd36c1836cd76a082",
            provenance={
                "upstream_pr_url": "https://github.com/catchorg/Catch2/pull/2723",
                "upstream_issue_url": "https://github.com/catchorg/Catch2/issues/2719",
                "license": "BSL-1.0",
            },
        ),
        common_row(
            task_id="simdjson-preserve-underflow-signed-zero-v2",
            user_prompt=simd_prompt,
            repository={
                "url": "https://github.com/simdjson/simdjson.git",
                "base_commit": "6d2a09f8e5d116b6bfcb2be21ce50d0048fa8fc4",
                "reference_commit": "b92cbbe280bce0aa404a273bf6e7dcf563556d33",
            },
            editable_file="include/simdjson/generic/numberparsing.h",
            hidden_validation=simd_hidden,
            dependency_identities={
                "simdjson-data": "a5b13babe65c1bba7186b41b43d4cbdc20a5c470"
            },
            reference_patch_sha256="fec2d0acf4e83a24875f13f012e849cff64c5e1f573faa3b7d44ef2c29cd01f2",
            provenance={
                "upstream_pr_url": "https://github.com/simdjson/simdjson/pull/1899",
                "upstream_issue_url": "https://github.com/simdjson/simdjson/issues/1898",
                "license": "Apache-2.0",
            },
        ),
    ]
    rows[0]["diagnostic_checklist"] = copy.deepcopy(LEGACY_FMT_PR_SOLUTION_CHECKLIST)
    return rows


def demo_fmtlib_prompt_suffix() -> str:
    return prompt(
        """
        # Implementation instructions for this demo lane

        The only model-editable production file is `include/fmt/chrono.h`. The evaluator
        also applies C++ regression tests in `test/chrono-test.cc`, but that `.cpp` file is
        not editable by the model and must remain untouched by your response. Treat those
        tests as the expected behavior specification for the header fix.

        The broken setup is this exact conversion path: formatting
        `std::chrono::time_point<std::chrono::system_clock, Duration>` narrows through the
        native `std::chrono::system_clock::duration` before calendar conversion. For wide or
        coarse `Duration` values such as milliseconds at year 3000, that intermediate native
        duration conversion can signed-overflow before `gmtime` or `localtime` receives a
        valid `time_t`. The fix must remove that native-duration narrowing path.

        Required changes in `include/fmt/chrono.h`:

        1. Add `detail::is_same_arithmetic_type<Rep1, Rep2>` with this exact category
           predicate: true when both reps are integral, or both reps are floating point. Do
           not implement this as exact same-type comparison; `int` and `long long` are the
           same arithmetic category for this purpose.
        2. Add two SFINAE overload families for `detail::fmt_duration_cast<To>(duration)`:
           one enabled for same arithmetic categories and one enabled for mixed categories.
           The same-category overload must, under `#if FMT_SAFE_DURATION_CAST`, call
           `safe_duration_cast::safe_duration_cast<To>(from, ec)`, throw
           `format_error("cannot format duration")` when `ec` is nonzero, and otherwise
           return the checked value. Under `#else`, return `std::chrono::duration_cast<To>`
           from the same helper. The mixed-category overload must always use
           `std::chrono::duration_cast<To>`. Avoid a generic unconstrained fallback that can
           be ambiguous with the integral/integral or float/float overloads.
        3. Place `fmt_duration_cast` only after the existing `safe_duration_cast` machinery is
           visible, so the helper can call `safe_duration_cast::safe_duration_cast<To>`.
        4. Add `detail::to_time_t(time_point<system_clock, Duration>)`. It must convert
           `time_point.time_since_epoch()` directly to `std::chrono::duration<std::time_t>`
           using `fmt_duration_cast` and return `.count()`. Do not call
           `std::chrono::system_clock::to_time_t` from this helper.
        5. Replace the existing `gmtime(time_point<system_clock>)` overload with a templated
           `gmtime(time_point<system_clock, Duration>)` overload that returns
           `gmtime(detail::to_time_t(time_point))`. Do not leave the old unsafe native-clock
           overload as the selected path for time-point formatting.
        6. In the `localtime(std::chrono::local_time<Duration>)` overload guarded by
           `FMT_USE_LOCAL_TIME`, replace `std::chrono::system_clock::to_time_t(
           std::chrono::current_zone()->to_sys(time))` with
           `detail::to_time_t(std::chrono::current_zone()->to_sys(time))`.
        7. In `write_fractional_seconds`, replace both raw `std::chrono::duration_cast` calls
           used for whole-second subtraction and subsecond precision conversion with
           `fmt_duration_cast`.
        8. Remove the old `fmt_safe_duration_cast` helper entirely and replace its callers
           with the unified `fmt_duration_cast` helper.
        9. In `get_milliseconds`, keep the existing structure and negative-duration behavior,
           but replace the safe-branch casts and fallback raw casts with `fmt_duration_cast`.
        10. In `chrono_formatter`, replace the macro-specific branch that assigns `s` with
            the single expression
            `s = fmt_duration_cast<seconds>(std::chrono::duration<rep, Period>(val));`.
        11. In `formatter<time_point<system_clock, Duration>>`, keep the existing
            fractional-second logic and the `duration is too small` guard. Only replace the
            nested raw duration casts with `detail::fmt_duration_cast`, replace the one-second
            conversion with `detail::fmt_duration_cast<Duration>(std::chrono::seconds(1))`,
            and replace both `gmtime(std::chrono::time_point_cast<std::chrono::seconds>(val))`
            calls with `gmtime(val)`. For the no-subseconds path, keep using
            `formatter<std::tm, Char>::format(...)`; do not switch it to `do_format(...,
            nullptr)`.
        12. In `formatter<local_time<Duration>>`, mirror the same minimal pattern: use
            `detail::fmt_duration_cast` for subsecond math, call `localtime(val)` directly,
            and keep `formatter<std::tm, Char>::format(...)` for the no-subseconds path.

        Avoid these known wrong solutions:

        - Do not output only analysis or a patch that cannot be applied. Make a real edit to
          `include/fmt/chrono.h`.
        - Do not modify `include/fmt/format.h` or `test/chrono-test.cc`.
        - Do not implement `is_same_arithmetic_type` as exact same-type only.
        - Do not add unconstrained `fmt_duration_cast` overloads that conflict with the
          same-category overloads.
        - Do not use `if constexpr`; this header must remain C++11-compatible.
        - Do not manually rewrite time-point formatter paths to compute `std::time_t t` and
          call `do_format(..., nullptr)`; preserve the existing formatter structure and only
          replace the unsafe casts/call sites.
        - Do not leave calls to
          `gmtime(std::chrono::time_point_cast<std::chrono::seconds>(val))` or
          `localtime(std::chrono::time_point_cast<std::chrono::seconds>(val))`.

        Additional compile-safety instructions verified against the upstream PR:

        - Define `detail::to_time_t` inside `namespace detail`, immediately after the
          `fmt_duration_cast` overloads and before `FMT_BEGIN_EXPORT`; the exported
          templated `gmtime` overload must be able to call
          `detail::to_time_t(time_point)` exactly.
        - `fmt_duration_cast` is a detail helper: code inside `namespace detail` may call
          `fmt_duration_cast<To>(...)`, but formatter specializations outside `detail` must
          call `detail::fmt_duration_cast<To>(...)`.
        - The root fix requires direct formatter calls to `gmtime(val)` and `localtime(val)`;
          no formatter path may keep `time_point_cast<std::chrono::seconds>(val)` before
          either calendar conversion.
        - Keep helper templates C++11-compatible with `FMT_ENABLE_IF`; do not use
          `if constexpr`, `requires`, concepts, unconstrained catch-all overloads, or
          formatter-local manual `std::time_t t` conversion logic.

        Evaluator `.cpp` behavior checks, already supplied outside the editable scope:

        - `test/chrono-test.cc` checks that a millisecond system-clock time point at Unix
          epoch second `32503680000` formats as exactly `3000-01-01`.
        - When `FMT_SAFE_DURATION_CAST` is enabled, it checks that an unrepresentable extreme
          same-category duration conversion throws `fmt::format_error` with the expected
          duration-formatting failure path instead of wrapping or silently succeeding.

        Executable benchmark passing requires all of these to hold: only
        `include/fmt/chrono.h` changes, CMake configure succeeds, `chrono-test` builds,
        `chrono-test` passes, the independent warning-clean C++11 UBSan probe compiles,
        and the probe exits successfully.

        """
    )


def demo_fmtlib_concrete_shapes_and_structural_locks() -> str:
    instructions = (
        (
            "B01",
            "Treat required changes 1-12 above as one atomic migration. Complete all twelve before optional adjustments, and never undo an earlier item while repairing a later one.",
        ),
        (
            "B02",
            "Insert is_same_arithmetic_type, both fmt_duration_cast overloads, and to_time_t as one contiguous block inside the already-open first namespace detail, immediately before the closing `}  // namespace detail` that directly precedes `FMT_BEGIN_EXPORT`.",
        ),
        (
            "B03",
            "Do not create a new namespace for that block and do not move it to a later detail reopening. Do not edit, replace, retype, or remove FMT_NOMACRO or the existing localtime_r, localtime_s, gmtime_r, and gmtime_s fallback functions.",
        ),
        (
            "B04",
            "Add `template <typename Duration>` immediately before the exported system-clock time-point gmtime overload; change only that overload's parameter and return expression, leaving `gmtime(std::time_t)` intact.",
        ),
        (
            "B05",
            "Use unqualified fmt_duration_cast only while lexically inside namespace detail. Formatter specializations after the detail namespace closes must use detail::fmt_duration_cast; exported gmtime and localtime must use detail::to_time_t.",
        ),
        (
            "B06",
            "Preserve every existing #if, #else, and #endif plus every namespace and function closing brace. In get_milliseconds keep both FMT_SAFE_DURATION_CAST branches and replace only their cast calls.",
        ),
        (
            "B07",
            "Before ending the edit, verify the full call-site ledger: two fractional casts, every get_milliseconds cast in both branches, the chrono_formatter seconds assignment, all system-clock subsecond/one-second casts plus both gmtime(val) calls, and both local-time subsecond casts plus both localtime(val) calls.",
        ),
        (
            "B08",
            "Make the production edit now. The harness compiles it after this response; if a second turn supplies one compiler diagnostic, repair that existing patch without redesigning it or dropping any completed migration item.",
        ),
    )
    if tuple(item[0] for item in instructions) != BASELINE_REPAIR_INSTRUCTION_IDS:
        raise ValueError("baseline repair instruction IDs do not match validator contract")
    return prompt(
        r'''
        # Concrete code shapes retained from the first demo prompt

        Add the following trait and overload bodies without changing their semantics. They belong
        in the exact namespace and declaration-order location specified by the compile-safety delta below.

        ```cpp
        template <typename Rep1, typename Rep2>
        struct is_same_arithmetic_type
            : public std::integral_constant<
                  bool,
                  (std::is_integral<Rep1>::value && std::is_integral<Rep2>::value) ||
                      (std::is_floating_point<Rep1>::value &&
                       std::is_floating_point<Rep2>::value)> {};
        ```

        ```cpp
        template <typename To, typename FromRep, typename FromPeriod,
                  FMT_ENABLE_IF(is_same_arithmetic_type<FromRep, typename To::rep>::value)>
        To fmt_duration_cast(std::chrono::duration<FromRep, FromPeriod> from) {
        #if FMT_SAFE_DURATION_CAST
          int ec;
          To to = safe_duration_cast::safe_duration_cast<To>(from, ec);
          if (ec) FMT_THROW(format_error("cannot format duration"));
          return to;
        #else
          return std::chrono::duration_cast<To>(from);
        #endif
        }
        ```

        ```cpp
        template <typename To, typename FromRep, typename FromPeriod,
                  FMT_ENABLE_IF(!is_same_arithmetic_type<FromRep, typename To::rep>::value)>
        To fmt_duration_cast(std::chrono::duration<FromRep, FromPeriod> from) {
          return std::chrono::duration_cast<To>(from);
        }
        ```

        ```cpp
        template <typename Duration>
        std::time_t to_time_t(
            std::chrono::time_point<std::chrono::system_clock, Duration> time_point) {
          return fmt_duration_cast<std::chrono::duration<std::time_t>>(
                     time_point.time_since_epoch())
              .count();
        }
        ```

        In the system-clock time-point formatter, preserve the original formatter structure. Use
        `do_format(gmtime(val), ctx, &subsecs)` in the fractional path and
        `format(gmtime(val), ctx)` in the no-fractional path. Mirror those calls with
        `localtime(val)` in the guarded local-time formatter.
        '''
    ) + "\n" + numbered_section(
        "# Baseline-preserving compile-safety delta", instructions
    ) + "\n"


def demo_fmtlib_compact_bestof4_prompt() -> str:
    path = REPO_ROOT / "reports/public-pr-prompt-ablation-r2/final-prompt.md"
    return path.read_text(encoding="utf-8")


def demo_fmtlib_failure_prioritized_prompt() -> str:
    path = REPO_ROOT / "reports/public-pr-prompt-ablation-r3/final-prompt.md"
    return path.read_text(encoding="utf-8")


def demo_fmtlib_final_cleanup_prompt() -> str:
    parent = demo_fmtlib_failure_prioritized_prompt()
    parent_sha256 = hashlib.sha256(parent.encode("utf-8")).hexdigest()
    if parent_sha256 != FINAL_CLEANUP_REPAIR_PARENT_PROMPT_SHA256:
        raise ValueError("v8 parent prompt digest does not match the frozen v7 prompt")
    return parent.rstrip() + "\n\n" + FINAL_CLEANUP_REPAIR_SUFFIX


def demo_fmtlib_compact_bestof4_tasks() -> list[dict[str, Any]]:
    row = copy.deepcopy(demo_fmtlib_compiler_repair_tasks()[0])
    prompt_text = demo_fmtlib_compact_bestof4_prompt()
    row["model_input"]["messages"][0]["content"] = prompt_text
    row["integrity"]["model_prompt_sha256"] = hashlib.sha256(
        prompt_text.encode("utf-8")
    ).hexdigest()
    row["run_policy"] = {
        "attempts": 2,
        "candidate_count": 4,
        "candidate_isolation": "fresh_prepared_repository_copy",
        "candidate_selection": "first_executable_pass_else_furthest_executable_stage",
        "stop_on_first_executable_pass": True,
        "pass_at_1": "any isolated initial candidate passes the executable oracle",
        "pass_at_2": "any isolated candidate passes after at most one compiler repair",
        "attempt_2_feedback_mode": COMPILER_FEEDBACK_MODE,
        "feedback_disclosure": COMPILER_FEEDBACK_DISCLOSURE,
        "temperature": 0.7,
        "repair_temperature": 0.2,
        "top_p": 1.0,
        "seeds": [1701, 1702, 1703, 1704],
        "max_completion_tokens": 32768,
        "thinking_mode": "disabled",
    }
    row["prompt_contract"] = {
        "schema_version": "public-pr-prompt-ablation-v2",
        "profile": COMPACT_REPAIR_PROMPT_PROFILE,
        "baseline_prompt_sha256": FIRST_DEMO_BASELINE_PROMPT_SHA256,
        "handoff_prompt_sha256": (
            "b3997db3f5148890b879db2807c9a3c8de6f5be0552954cef529d8110c86ed25"
        ),
        "preserved_baseline_mechanisms": list(
            FIRST_DEMO_BASELINE_PRESERVED_MECHANISMS
        ),
        "removed_sections": [
            "generic_w01_w38_repository_workflow",
            "generic_f01_f12_self_audit",
            "unavailable_compile_search_terminal_actions",
            "duplicate_behavior_and_score_language",
        ],
        "added_sections": [
            "handoff_compact_model_boundary",
            "baseline_helper_shapes",
            "exact_pre_export_detail_anchor",
            "finite_consumer_ledger",
            "ten_structural_audit_locks",
        ],
    }
    row["harness_instructions"] = {
        "schema_version": "public-pr-compiler-repair-harness-v2",
        "suite_mode": "fmtlib-compact-repair-bestof4",
        "task_count": 1,
        "candidate_count": 4,
        "candidate_seeds": [1701, 1702, 1703, 1704],
        "candidate_isolation": "fresh_prepared_repository_copy",
        "stop_on_first_executable_pass": True,
        "response_protocol": "aider_diff_workspace_edit",
        "edit_format": "diff",
        "aider_auto_lint": False,
        "aider_auto_test": False,
        "candidate_diff_source": "git_diff_against_evaluator_baseline",
        "editable_files": ["include/fmt/chrono.h"],
        "protected_files": ["test/chrono-test.cc", "include/fmt/format.h"],
        "attempt_2_feedback_mode": COMPILER_FEEDBACK_MODE,
        "attempt_2_feedback_disclosure": COMPILER_FEEDBACK_DISCLOSURE,
        "repair_temperature": 0.2,
        "candidate_selection": (
            "first executable pass; otherwise furthest executable stage without "
            "reference similarity or checklist selection"
        ),
        "strict_pass": (
            "scope, build, upstream chrono test, and independent probe must all pass"
        ),
        "private_test_output_disclosed": False,
        "artifacts": [
            "candidate-N/attempt-1-message.txt",
            "candidate-N/attempt-2-message.txt",
            "candidate-N/candidate-production.patch",
            "candidate-N/diagnostics.json",
            "candidate-N/task-receipt.json",
            "task-receipt.json",
        ],
    }
    row["demo_contract"] = {
        "schema_version": "public-pr-compact-repair-bestof4-demo-v1",
        "success_condition": (
            "executable oracle pass is authoritative; mechanism coverage is diagnostic only"
        ),
        "claim_template": (
            "One task was evaluated with up to four isolated candidates and at most "
            "one sanitized compiler-repair turn per candidate."
        ),
    }
    if tuple(
        f"C{index:02d}" for index in range(1, 11)
    ) != COMPACT_REPAIR_INSTRUCTION_IDS:
        raise ValueError("compact repair instruction IDs do not match validator contract")
    return [row]


def demo_fmtlib_compact_bestof4_thinking_tasks() -> list[dict[str, Any]]:
    """Emit the compact best-of-four contract with GLM thinking enabled."""
    row = copy.deepcopy(demo_fmtlib_compact_bestof4_tasks()[0])
    row["run_policy"]["thinking_mode"] = "enabled"
    row["harness_instructions"]["thinking_mode"] = "enabled"
    row["harness_instructions"]["thinking_request"] = {
        "transport": "openai_chat_completions_extra_body",
        "field": "chat_template_kwargs.enable_thinking",
        "value": True,
    }
    row["demo_contract"] = {
        **row["demo_contract"],
        "schema_version": "public-pr-compact-repair-bestof4-thinking-demo-v1",
        "claim_template": (
            "One task was evaluated with thinking enabled, up to four isolated "
            "candidates, and at most one sanitized compiler-repair turn per candidate."
        ),
    }
    return [row]


def demo_fmtlib_verified_mechanism_tasks() -> list[dict[str, Any]]:
    """Emit the thinking-on v6 lane with compile-gated mechanism evidence."""

    row = demo_fmtlib_compact_bestof4_thinking_tasks()[0]
    return [upgrade_thinking_row(row, LEGACY_FMT_PR_SOLUTION_CHECKLIST)]


def demo_fmtlib_prioritized_verified_mechanism_tasks() -> list[dict[str, Any]]:
    """Emit the thinking-on v7 lane with failure-prioritized prompt guidance."""

    row = copy.deepcopy(demo_fmtlib_verified_mechanism_tasks()[0])
    prompt_text = demo_fmtlib_failure_prioritized_prompt()
    row["model_input"]["messages"][0]["content"] = prompt_text
    row["integrity"]["model_prompt_sha256"] = hashlib.sha256(
        prompt_text.encode("utf-8")
    ).hexdigest()
    row["prompt_contract"] = {
        "schema_version": "public-pr-prompt-ablation-v3",
        "profile": PRIORITIZED_REPAIR_PROMPT_PROFILE,
        "baseline_prompt_sha256": FIRST_DEMO_BASELINE_PROMPT_SHA256,
        "parent_prompt_sha256": PRIORITIZED_REPAIR_PARENT_PROMPT_SHA256,
        "preserved_baseline_mechanisms": list(
            FIRST_DEMO_BASELINE_PRESERVED_MECHANISMS
        ),
        "removed_sections": [
            "generic_w01_w38_repository_workflow",
            "generic_f01_f12_self_audit",
            "ten_flat_c01_c10_audit_locks",
            "duplicate_behavior_and_scope_language",
        ],
        "added_sections": [
            "intern_file_map",
            "failure_conditioned_compile_blockers",
            "exact_reference_aligned_helper_shapes",
            "priority_ordered_consumer_ledger",
            "eight_priority_checks",
        ],
        "priority_check_ids": list(PRIORITIZED_REPAIR_INSTRUCTION_IDS),
        "failure_conditions": [
            "undeclared_duration_template_parameter",
            "helper_definition_outside_detail_namespace",
            "helper_use_before_declaration",
            "duration_passed_to_time_point_helper",
            "preprocessor_or_brace_boundary_deleted",
        ],
    }
    row["harness_instructions"] = {
        **row["harness_instructions"],
        "schema_version": "public-pr-compiler-repair-harness-v3",
        "suite_mode": "fmtlib-prioritized-verified-mechanisms-bestof4",
        "priority_check_ids": list(PRIORITIZED_REPAIR_INSTRUCTION_IDS),
    }
    row["demo_contract"] = {
        **row["demo_contract"],
        "schema_version": "public-pr-prioritized-bestof4-thinking-demo-v1",
        "claim_template": (
            "One task was evaluated with thinking enabled, up to four isolated "
            "candidates, one sanitized compiler-repair turn, and a "
            "failure-prioritized eight-check prompt."
        ),
    }
    return [row]


def demo_fmtlib_final_cleanup_verified_mechanism_tasks() -> list[dict[str, Any]]:
    """Emit the thinking-on v8 lane with one terminal legacy-helper cleanup gate."""

    row = copy.deepcopy(demo_fmtlib_prioritized_verified_mechanism_tasks()[0])
    prompt_text = demo_fmtlib_final_cleanup_prompt()
    row["model_input"]["messages"][0]["content"] = prompt_text
    row["integrity"]["model_prompt_sha256"] = hashlib.sha256(
        prompt_text.encode("utf-8")
    ).hexdigest()
    row["prompt_contract"] = {
        **row["prompt_contract"],
        "schema_version": "public-pr-prompt-ablation-v4",
        "profile": FINAL_CLEANUP_REPAIR_PROMPT_PROFILE,
        "parent_prompt_sha256": FINAL_CLEANUP_REPAIR_PARENT_PROMPT_SHA256,
        "added_sections": [
            *row["prompt_contract"]["added_sections"],
            "final_mandatory_legacy_helper_cleanup",
        ],
        "mandatory_cleanup": {
            "identifier_must_be_absent": "fmt_safe_duration_cast",
            "replacement_helper": "fmt_duration_cast",
            "required_after_consumer_migration": True,
            "preserve_adjacent_structure": True,
        },
    }
    row["harness_instructions"] = {
        **row["harness_instructions"],
        "schema_version": "public-pr-compiler-repair-harness-v4",
        "suite_mode": "fmtlib-final-cleanup-verified-mechanisms-bestof4",
    }
    row["demo_contract"] = {
        **row["demo_contract"],
        "schema_version": "public-pr-final-cleanup-bestof4-thinking-demo-v1",
        "claim_template": (
            "One task was evaluated with thinking enabled, up to four isolated "
            "candidates, one sanitized compiler-repair turn, and a final mandatory "
            "legacy-helper cleanup gate."
        ),
    }
    return [row]


def demo_fmtlib_compiler_repair_tasks() -> list[dict[str, Any]]:
    row = copy.deepcopy(tasks()[0])
    generic_prompt = row["model_input"]["messages"][0]["content"]
    base_prompt = generic_prompt.split("\n# Mandatory repository-edit workflow", 1)[0]
    base_prompt = base_prompt.replace(
        "Work directly in the supplied repository using Aider whole-file editing.",
        "Work directly in the supplied repository using Aider diff editing.",
    )
    prompt_text = (
        base_prompt.rstrip()
        + "\n\n"
        + demo_fmtlib_prompt_suffix().strip()
        + "\n\n"
        + demo_fmtlib_concrete_shapes_and_structural_locks().strip()
        + "\n"
    )
    row["model_input"]["messages"][0]["content"] = prompt_text
    row["model_input"]["response_protocol"] = "aider_diff_workspace_edit"
    row["output_contract"]["edit_format"] = "diff"
    row["integrity"]["model_prompt_sha256"] = hashlib.sha256(
        prompt_text.encode("utf-8")
    ).hexdigest()
    row["run_policy"] = {
        "attempts": 2,
        "pass_at_1": "initial repository state after the baseline-preserving prompt",
        "pass_at_2": "same repository after one sanitized compiler-feedback repair turn",
        "attempt_2_feedback_mode": COMPILER_FEEDBACK_MODE,
        "feedback_disclosure": COMPILER_FEEDBACK_DISCLOSURE,
        "temperature": 0.7,
        "repair_temperature": 0.2,
        "top_p": 1.0,
        "seeds": [1701],
        "max_completion_tokens": 32768,
        "thinking_mode": "disabled",
    }
    row["prompt_contract"] = {
        "schema_version": "public-pr-prompt-ablation-v1",
        "profile": BASELINE_REPAIR_PROMPT_PROFILE,
        "baseline_prompt_sha256": FIRST_DEMO_BASELINE_PROMPT_SHA256,
        "preserved_baseline_mechanisms": list(
            FIRST_DEMO_BASELINE_PRESERVED_MECHANISMS
        ),
        "removed_sections": [
            "generic_w01_w38_repository_workflow",
            "generic_f01_f12_self_audit",
            "demo_score_optimization_language",
        ],
        "added_sections": [
            "baseline_concrete_code_shapes",
            "eight_task_specific_structural_locks",
            "sanitized_compiler_repair_contract",
        ],
    }
    baseline = demo_fmtlib_single_turn_tasks()[0]
    row["diagnostic_checklist"] = copy.deepcopy(LEGACY_FMT_PR_SOLUTION_CHECKLIST)
    row["required_header_changes"] = copy.deepcopy(
        baseline["required_header_changes"]
    )
    row["wrong_solution_guards"] = copy.deepcopy(
        baseline["wrong_solution_guards"]
    )
    row["harness_instructions"] = {
        "schema_version": "public-pr-compiler-repair-harness-v1",
        "suite_mode": "fmtlib-compiler-repair",
        "attempts": 2,
        "response_protocol": "aider_diff_workspace_edit",
        "edit_format": "diff",
        "candidate_diff_source": "git_diff_against_evaluator_baseline",
        "editable_files": ["include/fmt/chrono.h"],
        "protected_files": ["test/chrono-test.cc", "include/fmt/format.h"],
        "attempt_2_feedback_mode": COMPILER_FEEDBACK_MODE,
        "attempt_2_feedback_disclosure": COMPILER_FEEDBACK_DISCLOSURE,
        "repair_temperature": 0.2,
        "strict_pass": "scope, build, upstream chrono test, and independent probe must all pass",
        "private_test_output_disclosed": False,
        "artifacts": [
            "attempt-1-message.txt",
            "attempt-2-message.txt",
            "candidate-production.patch",
            "diagnostics.json",
            "failure-log-tail.txt",
            "task-receipt.json",
        ],
    }
    row["hard_scope_gate"] = copy.deepcopy(baseline["hard_scope_gate"])
    row["demo_evaluation_policy"] = copy.deepcopy(
        baseline["demo_evaluation_policy"]
    )
    row["demo_contract"] = {
        "schema_version": "public-pr-compiler-repair-demo-v1",
        "success_condition": "executable oracle pass is authoritative; mechanism coverage is diagnostic",
        "claim_template": "Two-turn compiler-guided model patch changed only the target production file and was evaluated by the frozen executable oracle.",
    }
    return [row]


def demo_fmtlib_single_turn_tasks() -> list[dict[str, Any]]:
    row = copy.deepcopy(tasks()[0])
    base_prompt = row["model_input"]["messages"][0]["content"].replace(
        "Work directly in the supplied repository using Aider whole-file editing.",
        "Work directly in the supplied repository using Aider diff editing.",
    )
    prompt_text = base_prompt + "\n" + demo_fmtlib_prompt_suffix()
    row["model_input"]["messages"][0]["content"] = prompt_text
    row["model_input"]["response_protocol"] = "aider_diff_workspace_edit"
    row["output_contract"]["edit_format"] = "diff"
    row["integrity"]["model_prompt_sha256"] = hashlib.sha256(
        prompt_text.encode("utf-8")
    ).hexdigest()
    row["run_policy"] = {
        "attempts": 1,
        "pass_at_1": "initial repository state after the first model response",
        "feedback_disclosure": "none_single_turn_demo",
        "temperature": 0.7,
        "top_p": 1.0,
        "seeds": [1701],
        "max_completion_tokens": 32768,
        "thinking_mode": "disabled",
    }
    row["diagnostic_checklist"] = copy.deepcopy(LEGACY_FMT_PR_SOLUTION_CHECKLIST)
    row["required_header_changes"] = [
        {
            "id": "same-arithmetic-dispatch",
            "path": "include/fmt/chrono.h",
            "instruction": "Add detail::is_same_arithmetic_type<Rep1, Rep2> using integral/integral or floating/floating category logic.",
        },
        {
            "id": "fmt-duration-cast-helper",
            "path": "include/fmt/chrono.h",
            "instruction": "Add SFINAE detail::fmt_duration_cast<To> overloads for same-category and mixed-category casts.",
        },
        {
            "id": "safe-cast-placement",
            "path": "include/fmt/chrono.h",
            "instruction": "Place fmt_duration_cast after the existing safe_duration_cast machinery is visible.",
        },
        {
            "id": "to-time-t-helper",
            "path": "include/fmt/chrono.h",
            "instruction": "Add detail::to_time_t(time_point<system_clock, Duration>) with direct epoch-duration to time_t-duration conversion.",
        },
        {
            "id": "templated-gmtime",
            "path": "include/fmt/chrono.h",
            "instruction": "Replace gmtime(time_point<system_clock>) with templated gmtime(time_point<system_clock, Duration>).",
        },
        {
            "id": "localtime-to-time-t",
            "path": "include/fmt/chrono.h",
            "instruction": "Fix localtime(local_time<Duration>) to call detail::to_time_t(current_zone()->to_sys(time)).",
        },
        {
            "id": "fractional-seconds-casts",
            "path": "include/fmt/chrono.h",
            "instruction": "Use fmt_duration_cast in write_fractional_seconds().",
        },
        {
            "id": "remove-old-safe-helper",
            "path": "include/fmt/chrono.h",
            "instruction": "Remove old fmt_safe_duration_cast helper and replace its callers.",
        },
        {
            "id": "milliseconds-casts",
            "path": "include/fmt/chrono.h",
            "instruction": "Use fmt_duration_cast in get_milliseconds().",
        },
        {
            "id": "chrono-formatter-cast",
            "path": "include/fmt/chrono.h",
            "instruction": "Collapse chrono_formatter seconds conversion to fmt_duration_cast<seconds>(...).",
        },
        {
            "id": "time-point-root-fix",
            "path": "include/fmt/chrono.h",
            "instruction": "In formatter<time_point<system_clock, Duration>>, preserve structure but replace unsafe casts and call gmtime(val).",
        },
        {
            "id": "local-time-root-fix",
            "path": "include/fmt/chrono.h",
            "instruction": "In formatter<local_time<Duration>>, mirror the localtime(val) fix.",
        },
    ]
    row["wrong_solution_guards"] = [
        "Make a real edit to include/fmt/chrono.h; prose-only output is a failure.",
        "Do not modify test/chrono-test.cc.",
        "Do not modify include/fmt/format.h.",
        "Do not implement same-type-only arithmetic matching.",
        "Do not add unconstrained fmt_duration_cast overloads.",
        "Do not use if constexpr or other C++17-only syntax.",
        "Do not rewrite the no-subseconds formatter path to do_format(..., nullptr).",
        "Do not leave time_point_cast<seconds> before gmtime/localtime.",
    ]
    row["harness_instructions"] = {
        "schema_version": "public-pr-demo-harness-instructions-v1",
        "suite_mode": "fmtlib-demo",
        "attempts": 1,
        "response_protocol": "aider_diff_workspace_edit",
        "edit_format": "diff",
        "candidate_diff_source": "git_diff_against_evaluator_baseline",
        "editable_files": ["include/fmt/chrono.h"],
        "protected_files": ["test/chrono-test.cc", "include/fmt/format.h"],
        "hard_scope_gate": "changed_paths must be exactly a non-empty subset of editable_files; for this demo that means include/fmt/chrono.h must be changed and no other path may change",
        "strict_pass": "score.passed requires scope_passed, build_passed, and probe_passed",
        "demo_baseline_pass": "demo_baseline.passed is true if score.passed is true, or if at least 9 of 12 checklist items are present and line similarity is at least 0.75",
        "artifacts": [
            "candidate-production.patch",
            "upstream-reference.patch",
            "candidate-vs-reference diff",
            "diagnostics.json",
            "failure-log-tail.txt",
        ],
    }
    row["hard_scope_gate"] = {
        "schema_version": "public-pr-hard-scope-gate-v1",
        "require_nonempty_change": True,
        "required_changed_paths": ["include/fmt/chrono.h"],
        "allowed_changed_paths": ["include/fmt/chrono.h"],
        "forbidden_changed_paths": ["test/chrono-test.cc", "include/fmt/format.h"],
        "failure_class_when_empty": "no_production_change",
        "failure_class_when_forbidden_path_changes": "scope_violation",
    }
    row["demo_evaluation_policy"] = {
        "schema_version": "public-pr-demo-baseline-v1",
        "minimum_present_checklist_items": 9,
        "total_checklist_items": 12,
        "minimum_line_similarity_ratio": 0.75,
        "executable_oracle_override": "if score.passed is true, demo baseline is pass even when checklist wording differs",
        "mechanism_baseline": "if score.passed is false, demo baseline is pass when at least 9 of 12 PR mechanism checks are present and candidate/reference line similarity is at least 0.75",
        "interpretation_limit": "demo baseline is weaker than executable oracle; benchmark pass claims still require score.passed",
    }
    row["demo_contract"] = {
        "schema_version": "public-pr-single-turn-demo-v1",
        "claim_template": "Single-turn model patch changed only the target production file and either passed the executable oracle or met the 9-of-12 PR-mechanism demo baseline with low divergence.",
        "success_condition": "demo_baseline.passed is true; executable benchmark pass requires score.passed true",
    }
    return [row]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "configs/public_pr_eval/public-pr-repo-eval-v2.jsonl",
    )
    parser.add_argument(
        "--demo-fmtlib-single-turn",
        action="store_true",
        help="emit the one-task, one-attempt fmtlib public-PR demo contract",
    )
    parser.add_argument(
        "--demo-fmtlib-compiler-repair",
        action="store_true",
        help="emit the baseline-preserving two-turn fmtlib compiler-repair contract",
    )
    parser.add_argument(
        "--demo-fmtlib-compact-bestof4",
        action="store_true",
        help="emit the compact one-task best-of-four compiler-repair contract",
    )
    parser.add_argument(
        "--demo-fmtlib-compact-bestof4-thinking",
        action="store_true",
        help="emit the compact best-of-four contract with GLM thinking enabled",
    )
    parser.add_argument(
        "--demo-fmtlib-verified-mechanisms",
        action="store_true",
        help="emit the thinking-on v6 contract with compile-gated mechanisms",
    )
    parser.add_argument(
        "--demo-fmtlib-prioritized-verified-mechanisms",
        action="store_true",
        help="emit the thinking-on v7 contract with failure-prioritized guidance",
    )
    parser.add_argument(
        "--demo-fmtlib-final-cleanup-verified-mechanisms",
        action="store_true",
        help="emit the thinking-on v8 contract with a final cleanup gate",
    )
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite evaluation JSONL: {args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    modes = (
        args.demo_fmtlib_single_turn,
        args.demo_fmtlib_compiler_repair,
        args.demo_fmtlib_compact_bestof4,
        args.demo_fmtlib_compact_bestof4_thinking,
        args.demo_fmtlib_verified_mechanisms,
        args.demo_fmtlib_prioritized_verified_mechanisms,
        args.demo_fmtlib_final_cleanup_verified_mechanisms,
    )
    if sum(bool(mode) for mode in modes) > 1:
        raise ValueError("select only one demo output mode")
    if args.demo_fmtlib_final_cleanup_verified_mechanisms:
        selected = demo_fmtlib_final_cleanup_verified_mechanism_tasks()
    elif args.demo_fmtlib_prioritized_verified_mechanisms:
        selected = demo_fmtlib_prioritized_verified_mechanism_tasks()
    elif args.demo_fmtlib_verified_mechanisms:
        selected = demo_fmtlib_verified_mechanism_tasks()
    elif args.demo_fmtlib_compact_bestof4_thinking:
        selected = demo_fmtlib_compact_bestof4_thinking_tasks()
    elif args.demo_fmtlib_compact_bestof4:
        selected = demo_fmtlib_compact_bestof4_tasks()
    elif args.demo_fmtlib_compiler_repair:
        selected = demo_fmtlib_compiler_repair_tasks()
    elif args.demo_fmtlib_single_turn:
        selected = demo_fmtlib_single_turn_tasks()
    else:
        selected = tasks()
    payload = b"".join(canonical_json(row) for row in selected)
    args.output.write_bytes(payload)
    checksum = args.output.with_suffix(args.output.suffix + ".sha256")
    checksum.write_text(
        f"{hashlib.sha256(payload).hexdigest()}  {args.output.name}\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "rows": len(selected),
                "output": str(args.output),
                "sha256": hashlib.sha256(payload).hexdigest(),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
