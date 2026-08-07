#!/usr/bin/env python3
"""Freeze the exact 51-contract CHARM V1 curriculum before materialization."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


PROPOSAL_SCHEMA = "charm-v1-proposal-plan-v1"
CURRICULUM_SCHEMA = "charm-v1-curriculum-plan-v1"
DEPENDENCY_SCHEMA = "charm-v1-dependency-manifest-v1"
BATCH_ID = "charm-task-generation-v1-20260803T193513Z"
SESSION_ID = "charm-task-generation-v1-20260803T193513Z-25dfaec0-bdfe-4a72-84cf-7ef893badfb3"

# Each tuple is: task-id suffix, story/contract, exact public API, principal
# implementation strategy, and the five-or-more observable edge partitions.
FAMILIES: tuple[tuple[str, tuple[tuple[str, str, list[str], str, list[str]], ...]], ...] = (
    ("Allergies", (
        ("exposure-window-ledger", "Track named exposures with severity and minute stamps; query distinct active allergens inside an inclusive rolling window in lexical order.", ["namespace charm::allergy", "class ExposureWindowLedger", "void record(std::string,int,int)", "std::vector<std::string> active(int,int,int) const"], "retain immutable events and filter by time/severity into an ordered set", ["empty ledger", "window endpoints", "duplicate allergens", "severity threshold", "future records"]),
        ("dose-policy-table", "Maintain per-allergen cumulative dose limits and classify a batch without changing state when any dose is invalid.", ["namespace charm::allergy", "class DosePolicyTable", "bool set_limit(std::string,int)", "std::vector<std::string> exceeded(const std::vector<std::pair<std::string,int>>&) const"], "validated map updates plus batch aggregation", ["unknown allergen", "negative dose", "repeated batch key", "exact limit", "empty batch"]),
        ("rotating-sensitivity-mask", "Repair a rotating eight-bit sensitivity code whose logical allergen positions shift by a normalized offset and ignore bits above the low byte.", ["namespace charm::allergy", "class SensitivityMask", "SensitivityMask(unsigned,int)", "bool reacts_to(std::string_view) const", "std::vector<std::string> reactions() const"], "mask low byte, normalize rotation, and map fixed public names", ["zero mask", "negative rotation", "large rotation", "high ignored bits", "reaction order"]),
    )),
    ("Bank Account", (
        ("idempotent-cent-ledger", "Apply uniquely identified cent transactions exactly once, reject overdrafts atomically, and expose a chronological accepted ledger.", ["namespace charm::bank", "class CentLedger", "bool apply(std::string,long long)", "long long balance() const", "std::vector<std::string> accepted_ids() const"], "set-backed idempotence with checked integer balance transition", ["duplicate id", "exact withdrawal", "overdraft", "zero transaction", "overflow boundary"]),
        ("atomic-transfer-plan", "Validate and execute a transfer plan across named accounts atomically; any missing account, negative amount, or insufficient source leaves every balance unchanged.", ["namespace charm::bank", "struct Transfer { std::string from; std::string to; long long cents; }", "class AccountBook", "bool execute(const std::vector<Transfer>&)", "long long balance_of(std::string_view) const"], "simulate deltas then commit once all constraints pass", ["self transfer", "missing account", "chained funding", "insufficient aggregate", "empty plan"]),
        ("checkpointed-overdraft", "Repair an account with checkpoints so rollback restores balance and fee count; a withdrawal below the limit is rejected without charging a fee.", ["namespace charm::bank", "class CheckpointAccount", "std::size_t checkpoint()", "bool withdraw(long long)", "void deposit(long long)", "bool rollback(std::size_t)", "long long balance() const"], "append snapshots and truncate later history on rollback", ["invalid checkpoint", "exact limit", "rejected withdrawal", "rollback twice", "deposit after rollback"]),
    )),
    ("Binary Search Tree", (
        ("ranked-multiset-tree", "Store duplicate integers in a search tree and answer zero-based kth and strict-less-than rank queries after single-occurrence erasure.", ["namespace charm::bst", "class RankedTree", "void insert(int)", "bool erase_one(int)", "std::optional<int> kth(std::size_t) const", "std::size_t rank(int) const"], "subtree multiplicities and sizes maintained across deletion", ["empty tree", "duplicates", "root deletion", "out-of-range kth", "absent erase"]),
        ("interval-coverage-tree", "Index closed integer intervals by start and return all labels containing a query point ordered by shortest interval then label.", ["namespace charm::bst", "class IntervalIndex", "bool add(int,int,std::string)", "std::vector<std::string> containing(int) const"], "ordered start index with deterministic filtered ranking", ["reversed interval", "shared endpoint", "same length tie", "negative coordinates", "no matches"]),
        ("duplicate-side-traversal", "Repair a tree whose duplicate placement policy is configurable per instance and whose preorder traversal must preserve that policy after moves.", ["namespace charm::bst", "enum class DuplicateSide { left, right }", "class PolicyTree", "explicit PolicyTree(DuplicateSide)", "void insert(int)", "std::vector<int> preorder() const"], "unique ownership nodes with policy-aware iterative insertion", ["single node", "all equal", "left policy", "right policy", "zig-zag values"]),
    )),
    ("Circular Buffer", (
        ("generation-overwrite-ring", "A fixed-capacity overwrite ring returns generation-tagged handles; overwritten handles become invalid and snapshots remain oldest-first.", ["namespace charm::ring", "struct Handle { std::size_t slot; std::size_t generation; }", "class OverwriteRing", "Handle push(int)", "std::optional<int> read(Handle) const", "std::vector<int> snapshot() const"], "slot generations plus head/count ring arithmetic", ["zero capacity", "first wrap", "stale handle", "multiple wraps", "capacity one"]),
        ("reserve-commit-ring", "Reserve write slots with tokens, commit or cancel them, and expose only committed values in reservation order without blocking.", ["namespace charm::ring", "class CommitRing", "std::optional<std::size_t> reserve()", "bool commit(std::size_t,int)", "bool cancel(std::size_t)", "std::optional<int> pop()"], "token state machine over bounded slots", ["full reservations", "cancel head", "out-of-order commit", "stale token", "empty pop"]),
        ("wrapped-slice-repair", "Repair logical slicing of a wrapped ring: negative starts count from the logical end and lengths clamp without exposing unused storage.", ["namespace charm::ring", "class SliceRing", "void push(int)", "std::vector<int> slice(long long,std::size_t) const", "std::size_t size() const"], "translate normalized logical indices through physical head", ["negative start", "start past end", "oversized length", "partially full", "wrapped full"]),
    )),
    ("Clock", (
        ("offset-civil-clock", "Represent a local minute and UTC offset, normalize arbitrary inputs, and compare instants while preserving each clock's displayed offset.", ["namespace charm::clockwork", "class OffsetClock", "static OffsetClock at(long long,long long,int)", "OffsetClock plus_minutes(long long) const", "bool same_instant(const OffsetClock&) const", "std::string display() const"], "floor-mod local minutes and convert through offset", ["negative time", "large additions", "half-hour offset", "midnight crossing", "same instant different display"]),
        ("weekly-window-intersection", "Intersect recurring half-open weekly minute windows, splitting wraparound inputs and returning normalized non-touching segments.", ["namespace charm::clockwork", "struct Window { int begin; int end; }", "std::vector<Window> intersect_weekly(Window,Window)"], "normalize into linear segments, intersect, merge only overlap", ["empty window", "full wrap", "touching endpoints", "two-piece result", "invalid minute"]),
        ("wrapped-elapsed-counter", "Repair elapsed-minute computation for a wrapping 24-hour counter with an explicit wrap count and reject inconsistent observations.", ["namespace charm::clockwork", "std::optional<long long> elapsed(int start_minute,int end_minute,long long wraps)"], "validate day-minute domain and derive signed-safe total", ["same minute no wrap", "same minute one wrap", "midnight crossing", "negative wraps", "invalid minute"]),
    )),
    ("Complex Numbers", (
        ("stable-complex-quotient", "Implement finite rectangular complex arithmetic with a scale-safe quotient and approximate equality using absolute plus relative tolerance.", ["namespace charm::complex", "class StableComplex", "double real() const", "double imag() const", "StableComplex operator+(StableComplex) const", "std::optional<StableComplex> divided_by(StableComplex) const", "bool near(StableComplex,double,double) const"], "Smith-style scaled division and componentwise tolerance", ["zero divisor", "huge imaginary divisor", "tiny components", "NaN input", "relative tolerance"]),
        ("complex-polynomial", "Evaluate a complex polynomial and its derivative together using one Horner pass over descending coefficients.", ["namespace charm::complex", "struct PairValue { std::complex<double> value; std::complex<double> derivative; }", "PairValue evaluate_with_derivative(const std::vector<std::complex<double>>&,std::complex<double>)"], "extended Horner recurrence", ["empty coefficients", "constant", "zero point", "imaginary coefficients", "high degree"]),
        ("polar-mean-repair", "Repair the mean direction of weighted complex phasors; negative weights invalidate the batch and a zero resultant has no direction.", ["namespace charm::complex", "std::optional<double> weighted_direction(const std::vector<std::pair<std::complex<double>,double>>& )"], "weighted vector sum followed by normalized atan2", ["empty batch", "negative weight", "zero weights", "opposite cancellation", "angle branch cut"]),
    )),
    ("Crypto Square", (
        ("keyed-square-transposition", "Normalize ASCII alphanumerics, place them in a near-square grid, rotate columns by a validated key permutation, and join rows with spaces.", ["namespace charm::cryptosquare", "std::optional<std::string> encode_keyed(std::string_view,const std::vector<std::size_t>&)"], "near-square dimensions plus inverse-free column permutation", ["empty text", "invalid key duplicate", "ragged final row", "punctuation only", "mixed case"]),
        ("streaming-square-encoder", "Accept text chunks, freeze dimensions only at finish, and make finish idempotently return the same rectangular column encoding.", ["namespace charm::cryptosquare", "class StreamingEncoder", "bool append(std::string_view)", "std::string finish()", "bool finished() const"], "buffer normalized bytes then one terminal layout", ["empty chunks", "append after finish", "finish twice", "perfect square", "one-character input"]),
        ("ragged-square-decoder", "Repair decoding of whitespace-separated ragged columns while rejecting impossible column-height patterns rather than fabricating padding.", ["namespace charm::cryptosquare", "std::optional<std::string> decode_columns(std::string_view)"], "validate monotone column lengths and traverse original rows", ["empty input", "extra spaces", "height gap", "single column", "ragged valid columns"]),
    )),
    ("Diamond", (
        ("styled-hollow-diamond", "Render a centered odd-height hollow diamond with caller-selected edge/background characters and no trailing spaces.", ["namespace charm::diamond", "std::optional<std::vector<std::string>> render_hollow(int,char,char)"], "row distance geometry with right trimming", ["height one", "even height", "same edge/background", "wide diamond", "trailing-space rule"]),
        ("manhattan-shell", "Enumerate integer grid points at exact Manhattan radius around a center, clockwise from the top, without duplicates.", ["namespace charm::diamond", "struct Point { int x; int y; bool operator==(const Point&) const = default; }", "std::vector<Point> shell(Point,int)"], "four directed edge walks with corner ownership", ["radius zero", "negative radius", "ordering", "negative center", "radius two corners"]),
        ("clipped-diamond-repair", "Repair clipping of a filled Manhattan diamond to a half-open viewport and return occupied cells row-major in viewport coordinates.", ["namespace charm::diamond", "struct Rect { int x0; int y0; int x1; int y1; }", "std::vector<std::pair<int,int>> clipped_cells(int,int,int,Rect)"], "iterate clipped bounds and test Manhattan membership", ["empty viewport", "negative radius", "fully outside", "boundary tangent", "nonzero origin"]),
    )),
    ("Grade School", (
        ("moving-roster", "Maintain one grade per student, move existing students atomically, and list grade members and the whole school in deterministic order.", ["namespace charm::school", "class MovingRoster", "bool enroll(std::string,int)", "bool move(std::string,int)", "std::vector<std::string> grade(int) const", "std::vector<std::pair<int,std::string>> roster() const"], "bidirectional name-to-grade and ordered-grade indexes", ["duplicate enroll", "absent move", "same-grade move", "empty grade", "lexical ordering"]),
        ("weighted-gradebook", "Store weighted assessments, replace scores by assessment ID, and rank students by rounded basis-point average with lexical ties.", ["namespace charm::school", "class WeightedGradebook", "bool set(std::string,std::string,int,int)", "std::optional<int> average_bp(std::string_view) const", "std::vector<std::string> ranking() const"], "per-student keyed assessments and integer rational accumulation", ["zero weight", "score bounds", "replacement", "rounding tie", "student without scores"]),
        ("attendance-transaction-repair", "Repair batch attendance updates so duplicate names or unknown students reject the whole batch and day totals never partially change.", ["namespace charm::school", "class AttendanceBook", "bool add_student(std::string)", "bool record_day(const std::vector<std::pair<std::string,bool>>&)", "std::pair<int,int> totals(std::string_view) const"], "prevalidate batch identities then commit counters", ["duplicate batch name", "unknown student", "empty day", "all absent", "rejected batch rollback"]),
    )),
    ("Kindergarten Garden", (
        ("variable-cup-garden", "Parse multiple plant rows with a configurable cups-per-student value and return each named student's plants in row-major cup order.", ["namespace charm::garden", "class CupGarden", "static std::optional<CupGarden> parse(std::vector<std::string>,std::vector<std::string>,std::size_t)", "std::vector<char> plants(std::string_view) const"], "validate rectangular rows and index sorted unique students", ["duplicate student", "row width mismatch", "unknown student", "one cup", "multiple rows"]),
        ("rotating-garden-seats", "Rotate student ownership by day while plant positions stay fixed; negative days rotate backward with floor-mod semantics.", ["namespace charm::garden", "class RotatingGarden", "RotatingGarden(std::vector<std::string>,std::vector<char>)", "std::vector<char> plants_for(std::string_view,long long) const"], "stable sorted students with modular owner-to-position mapping", ["negative day", "large day", "unknown student", "empty garden", "duplicate names"]),
        ("garden-patch-repair", "Repair rectangular patch queries over a plant grid, clipping coordinates while rejecting reversed rectangles and unknown plant codes.", ["namespace charm::garden", "class PatchGrid", "static std::optional<PatchGrid> parse(const std::vector<std::string>&,std::string_view)", "std::map<char,int> count_patch(int,int,int,int) const"], "validated grid plus clipped half-open rectangle aggregation", ["reversed rectangle", "outside grid", "partial clip", "invalid code", "empty patch"]),
    )),
    ("Linked List", (
        ("splice-handle-list", "A move-only list issues generation handles, supports range splicing within the list, and invalidates only erased-node handles.", ["namespace charm::list", "struct NodeHandle { std::size_t id; std::size_t generation; }", "class SpliceList", "NodeHandle push_back(int)", "bool erase(NodeHandle)", "bool splice_before(NodeHandle,NodeHandle,NodeHandle)", "std::vector<int> values() const"], "stable node IDs with explicit order links and generations", ["stale handle", "empty range", "destination inside range", "erase endpoint", "move-only ownership"]),
        ("cursor-gap-list", "Edit a sequence through a movable gap cursor; inserts occur before the cursor and erase removes the next item without invalidating cursor position.", ["namespace charm::list", "class GapList", "bool move(long long)", "void insert(int)", "std::optional<int> erase_next()", "std::vector<int> values() const", "std::size_t cursor() const"], "two-vector gap representation", ["move before begin", "move past end", "insert at end", "erase at end", "alternating edits"]),
        ("stable-partition-repair", "Repair in-place stable partitioning of a singly linked list by a threshold while preserving node identity and relative order in both partitions.", ["namespace charm::list", "class StableList", "void push_back(int)", "void partition(int)", "std::vector<int> values() const"], "detach nodes into two chains then concatenate", ["empty list", "all low", "all high", "duplicates at threshold", "alternating values"]),
    )),
    ("Parallel Letter Frequency", (
        ("bounded-shard-frequency", "Count ASCII letters case-insensitively across documents using at most a requested worker count and return deterministic counts.", ["namespace charm::frequency", "std::array<std::size_t,26> count_bounded(const std::vector<std::string>&,std::size_t)"], "bounded atomic work index with private arrays and ordered reduction", ["zero workers", "more workers than docs", "nonletters", "empty docs", "mixed case"]),
        ("mergeable-frequency", "Accumulate byte-letter frequencies in independent shards and merge each shard at most once using a stable shard identifier.", ["namespace charm::frequency", "class MergeCounter", "bool merge(std::string,const std::array<std::size_t,26>&)", "std::size_t count(char) const", "std::size_t merged_shards() const"], "mutex-protected seen set and checked counters", ["duplicate shard", "invalid query char", "counter overflow", "empty shard id", "concurrent merges"]),
        ("partition-frequency-repair", "Repair deterministic partitioning so every document is counted exactly once even when workers exceed inputs or a chunk is empty.", ["namespace charm::frequency", "std::map<char,std::size_t> count_partitioned(const std::vector<std::string>&,std::size_t)"], "ceil-div contiguous partitions with future reduction", ["zero workers", "empty input", "workers exceed docs", "uneven split", "punctuation"]),
    )),
    ("Phone Number", (
        ("extension-canonicalizer", "Canonicalize a North-American number with an optional extension marker, rejecting misplaced letters and invalid exchange prefixes.", ["namespace charm::phone", "struct CanonicalPhone { std::string number; std::string extension; }", "std::optional<CanonicalPhone> canonicalize(std::string_view)"], "single pass separator grammar followed by NANP validation", ["country prefix", "extension x", "empty extension", "letter in number", "exchange starts zero"]),
        ("dial-plan-router", "Choose the longest matching digit prefix from a routing table and return the route plus unmatched subscriber digits.", ["namespace charm::phone", "class DialPlan", "bool add(std::string,std::string)", "std::optional<std::pair<std::string,std::string>> route(std::string_view) const"], "validated prefix trie with longest terminal", ["duplicate prefix", "nondigit input", "no match", "exact prefix", "overlapping prefixes"]),
        ("vanity-number-repair", "Repair vanity-number normalization using the classic keypad while preserving an optional leading plus only for an eleven-digit result.", ["namespace charm::phone", "std::optional<std::string> normalize_vanity(std::string_view)"], "ASCII keypad mapping then length/prefix validation", ["lowercase letters", "Q and Z", "misplaced plus", "ten digits", "eleven-digit wrong country"]),
    )),
    ("Spiral Matrix", (
        ("rectangular-spiral-fill", "Fill an arbitrary rows-by-columns matrix clockwise from a selected corner using a caller-provided starting value and step.", ["namespace charm::spiral", "enum class Corner { top_left, top_right, bottom_right, bottom_left }", "std::vector<std::vector<long long>> fill(std::size_t,std::size_t,Corner,long long,long long)"], "direction table rotated by corner with shrinking bounds", ["zero dimension", "single row", "single column", "negative step", "non-square"]),
        ("obstacle-spiral-walk", "Walk unblocked cells clockwise, turning on obstacles or visited cells, and stop when no adjacent unvisited cell remains.", ["namespace charm::spiral", "struct Cell { int row; int col; bool operator==(const Cell&) const = default; }", "std::vector<Cell> walk(const std::vector<std::string>&,Cell)"], "visited grid and four-direction turn attempts", ["blocked start", "ragged grid", "isolated start", "interior obstacle", "unreachable region"]),
        ("layer-view-repair", "Repair extraction of a zero-based rectangular perimeter layer without duplicating corners or underflowing thin interiors.", ["namespace charm::spiral", "std::vector<int> layer_clockwise(const std::vector<std::vector<int>>&,std::size_t)"], "validate rectangle then traverse four guarded edges", ["ragged matrix", "single cell layer", "single row layer", "single column layer", "layer out of range"]),
    )),
    ("Sublist", (
        ("wildcard-segment-relation", "Classify two integer patterns as equal, proper subpattern, proper superpattern, or unequal where a designated wildcard matches one value.", ["namespace charm::sublist", "enum class Relation { equal, subpattern, superpattern, unequal }", "Relation wildcard_relation(const std::vector<int>&,const std::vector<int>&,int)"], "directional sliding match with explicit exact equality", ["empty patterns", "all wildcards", "overlap", "properness", "wildcard value literal"]),
        ("cyclic-window-containment", "Find the earliest start where a pattern occurs in a circular host, forbidding matches longer than the host except both empty.", ["namespace charm::sublist", "std::optional<std::size_t> cyclic_find(const std::vector<int>&,const std::vector<int>&)"], "bounded modular comparison over each host start", ["both empty", "empty needle", "needle too long", "wrap match", "multiple starts"]),
        ("tolerant-subsequence-repair", "Repair ordered subsequence matching where each pair may differ by at most a nonnegative tolerance and return matched host indices.", ["namespace charm::sublist", "std::optional<std::vector<std::size_t>> tolerant_subsequence(const std::vector<long long>&,const std::vector<long long>&,long long)"], "greedy earliest valid indices with overflow-safe difference", ["negative tolerance", "empty needle", "large integers", "repeated host values", "no match"]),
    )),
    ("Yacht", (
        ("configurable-dice-score", "Score validated dice against a category object supporting exact-count groups, straights over a range, and sum-of-value rules.", ["namespace charm::yacht", "enum class RuleKind { exact_group, straight, value_sum }", "struct Category { RuleKind kind; int argument; }", "std::optional<int> score(const std::vector<int>&,int,Category)"], "frequency table plus rule-specific validation", ["invalid face", "wrong dice count", "duplicate straight", "missing group", "value sum"]),
        ("scorecard-assignment", "Assign rolls to distinct categories for maximum total score and return the lexicographically smallest category-index assignment on ties.", ["namespace charm::yacht", "struct Assignment { int total; std::vector<std::size_t> categories; }", "std::optional<Assignment> optimize(const std::vector<std::vector<int>>&,const std::vector<Category>&,int)"], "bitmask dynamic programming with explicit tie comparison", ["more rolls than categories", "invalid roll", "zero rolls", "equal total tie", "unscorable category"]),
        ("joker-rule-repair", "Repair a five-dice score function with at most one zero-valued joker that may replace any face consistently for the chosen category.", ["namespace charm::yacht", "enum class JokerCategory { yacht, full_house, four_kind, choice }", "std::optional<int> joker_score(const std::array<int,5>&,JokerCategory)"], "enumerate six joker substitutions and maximize valid category score", ["two jokers", "invalid face", "joker yacht", "full-house ambiguity", "choice with joker"]),
    )),
    ("Zebra Puzzle", (
        ("house-constraint-engine", "Solve a small house-order puzzle from equality, adjacency, and left-of constraints and report a solution only when it is unique.", ["namespace charm::zebra", "enum class ClueKind { same_house, adjacent, immediately_left }", "struct Clue { ClueKind kind; std::string a; std::string b; }", "std::optional<std::map<std::string,int>> solve_unique(int,const std::vector<std::vector<std::string>>&,const std::vector<Clue>&)"], "category permutation backtracking with early clue pruning", ["unknown item", "duplicate item", "no solution", "multiple solutions", "edge adjacency"]),
        ("solution-certificate", "Verify a proposed house assignment against category membership and clues, returning stable indices of every violated clue.", ["namespace charm::zebra", "struct Verification { bool complete; std::vector<std::size_t> violated; }", "Verification verify(int,const std::vector<std::vector<std::string>>&,const std::vector<Clue>&,const std::map<std::string,int>&)"], "validate bijections then evaluate each clue independently", ["missing assignment", "out-of-range house", "category collision", "unknown clue item", "multiple violations"]),
        ("contradiction-core-repair", "Repair contradiction detection to return an inclusion-minimal stable clue-index core, or an empty vector when the puzzle remains satisfiable.", ["namespace charm::zebra", "std::vector<std::size_t> contradiction_core(int,const std::vector<std::vector<std::string>>&,const std::vector<Clue>&)"], "deletion-based minimization around a deterministic satisfiability solver", ["satisfiable input", "single bad clue", "two independent conflicts", "invalid clue", "stable index order"]),
    )),
)

ROLE_SEQUENCE = (["direct_verified_success"] * 27 + ["boundary_case"] * 10
                 + ["repair_trajectory"] * 11 + ["calibration"] * 3)
STARTER_SEQUENCE = (["empty"] * 10 + ["skeleton"] * 13 + ["partial_implementation"] * 10
                    + ["semantic_bug"] * 8 + ["compile_bug"] * 5 + ["near_correct"] * 5)
HEADER_SEQUENCE = (["frozen"] * 11 + ["editable"] * 10 + ["reconstructed"] * 10
                   + ["repaired"] * 10 + ["extended"] * 10)
REPAIR_TYPES = ("compile_repair", "linker_repair", "api_repair", "hidden_test_repair", "runtime_repair", "sanitizer_repair")


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def build() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    role_counts: dict[str, int] = {}
    starter_counts: dict[str, int] = {}
    header_counts: dict[str, int] = {}
    layout_counts = {"cpp_only": 0, "header_only": 0, "header_and_cpp": 0, "multi_file_gt2": 0}
    repair_index = 0
    for family_index, (topic, specs) in enumerate(FAMILIES):
        for slot_index, (suffix, contract, api, strategy, edge_cases) in enumerate(specs, 1):
            index = family_index * 3 + slot_index - 1
            role = ROLE_SEQUENCE[(index * 19) % 51]
            starter = STARTER_SEQUENCE[(index * 31) % 51]
            header_mode = HEADER_SEQUENCE[(index * 37) % 51]
            if slot_index == 1:
                layout = "header_and_cpp"
                editable_files = [f"{suffix}.h", f"{suffix}.cpp"]
            elif slot_index == 2:
                layout = "cpp_only"
                editable_files = [f"{suffix}.cpp"]
            elif family_index < 8:
                layout = "header_only"
                editable_files = [f"{suffix}.hpp"]
            else:
                layout = "header_and_cpp"
                editable_files = [f"{suffix}.h", f"{suffix}.cpp"]
            if slot_index == 1 and family_index < 6:
                editable_files.append(f"{suffix}_detail.cpp")
                layout_counts["multi_file_gt2"] += 1
            layout_counts[layout] += 1
            role_counts[role] = role_counts.get(role, 0) + 1
            starter_counts[starter] = starter_counts.get(starter, 0) + 1
            header_counts[header_mode] = header_counts.get(header_mode, 0) + 1
            repair_type = None
            if role == "repair_trajectory":
                repair_type = REPAIR_TYPES[repair_index % len(REPAIR_TYPES)]
                repair_index += 1
            task_id = f"charm-v1-{suffix}"
            proposal = {
                "task_id": task_id,
                "topic": topic,
                "slot_id": str(slot_index),
                "story": contract,
                "contract": contract,
                "public_api": api,
                "starter_design": f"{starter} starter requiring {layout} action; header mode {header_mode}",
                "target_design": f"Complete the exact API using {strategy}; whole-file output for {', '.join(editable_files)}.",
                "oracle_design": "Five independent partitions: input validation, nominal behavior, boundary state, repeated transition, and determinism/ordering.",
                "solution_strategy": strategy,
                "edge_cases": edge_cases,
                "role": role,
                "starter_type": starter,
                "header_mode": header_mode,
                "editable_layout": layout,
                "editable_files": editable_files,
                "multi_file_gt2": len(editable_files) > 2,
                "api_capabilities": (["preserve_api", "implement_missing_api", "extend_api"]
                                     if slot_index == 1 else
                                     ["preserve_api", "repair_api", "refactor_api"]
                                     if slot_index == 2 else
                                     ["preserve_api", "extend_api", "refactor_api"]),
                "repair_type": repair_type,
                "difficulty": ("medium" if slot_index == 1 else "hard" if slot_index == 2 else "medium-hard"),
                "dependencies": ["c++17-standard-library"],
                "portability": "locked GCC image plus host Clang portability lane",
                "response_budget_bytes": 32768,
                "source_kind": "recovered_organic_failure_anchor" if index == 0 else "synthetic",
            }
            proposal["proposal_sha256"] = sha256_bytes(canonical_bytes(proposal))
            proposals.append(proposal)
    assert len(proposals) == 51
    plan = {
        "schema_version": PROPOSAL_SCHEMA,
        "protocol_id": "task-generation-v1",
        "generation_batch_id": BATCH_ID,
        "generation_session_id": SESSION_ID,
        "topics": [topic for topic, _ in FAMILIES],
        "tasks_per_topic": 3,
        "proposals": proposals,
    }
    curriculum = {
        "schema_version": CURRICULUM_SCHEMA,
        "generation_batch_id": BATCH_ID,
        "generation_session_id": SESSION_ID,
        "authorized_task_count": 51,
        "role_counts": role_counts,
        "starter_type_counts": starter_counts,
        "header_mode_counts": header_counts,
        "editable_layout_counts": layout_counts,
        "api_capability_counts": {
            capability: sum(capability in proposal["api_capabilities"] for proposal in proposals)
            for capability in ("implement_missing_api", "preserve_api", "extend_api", "repair_api", "refactor_api")
        },
        "repair_type_counts": {
            repair_type: sum(proposal["repair_type"] == repair_type for proposal in proposals)
            for repair_type in REPAIR_TYPES
        },
        "family_count": 17,
        "tasks_per_family": 3,
        "non_synthetic_direct_success_count": sum(
            proposal["source_kind"] != "synthetic" and proposal["role"] == "direct_verified_success"
            for proposal in proposals
        ),
        "training_canary": {"authorized": False, "frozen_task_count": 20, "epochs": 5, "matched_trials": 4},
    }
    dependencies = {
        "schema_version": DEPENDENCY_SCHEMA,
        "generation_batch_id": BATCH_ID,
        "environment_manifest": "dataset/configs/charm-v1-cpp17-environment.json",
        "task_count": 51,
        "external_packages": [],
        "tasks": [{
            "task_id": proposal["task_id"],
            "topic": proposal["topic"],
            "required_language": "c++17",
            "dependencies": proposal["dependencies"],
            "preflight_required": True,
        } for proposal in proposals],
        "all_task_preflight_policy": "compile one exact package probe per task; sampling forbidden",
    }
    return plan, curriculum, dependencies


def atomic_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(canonical_bytes(value))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    plan, curriculum, dependencies = build()
    outputs = {
        "v1-proposal-plan.json": plan,
        "v1-curriculum-plan.json": curriculum,
        "v1-dependency-manifest.json": dependencies,
    }
    for name, value in outputs.items():
        path = args.output_dir / name
        if path.exists():
            raise SystemExit(f"refusing to overwrite frozen V1 plan artifact: {path}")
        atomic_write(path, value)
    print(json.dumps({name: sha256_bytes((args.output_dir / name).read_bytes()) for name in outputs}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
