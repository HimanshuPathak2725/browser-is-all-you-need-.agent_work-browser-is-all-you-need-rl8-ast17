#!/usr/bin/env python3
"""Freeze the clean-room four-topic/60-task CHARM proposal plan.

This owner writes proposal and curriculum artifacts only.  It never writes task
roots.  Materialization remains blocked until repository-wide uniqueness,
atomic task-ID reservation, and cumulative pre-generation admission all pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


PROTOCOL_ID = "task-generation-four-topic-60-v1"
TOPICS = ("Clock", "Complex Numbers", "Spiral Matrix", "Zebra Puzzle")
TASKS_PER_TOPIC = 15
TASK_COUNT = len(TOPICS) * TASKS_PER_TOPIC


@dataclass(frozen=True)
class Proposal:
    topic: str
    slot_id: str
    slug: str
    title: str
    public_api: str
    contract: str
    starter_design: str
    target_design: str
    oracle_design: str
    solution_strategy: str
    edge_cases: tuple[str, ...]
    mechanism: str


def p(
    topic: str,
    slot: int,
    slug: str,
    title: str,
    public_api: str,
    contract: str,
    strategy: str,
    edge_cases: tuple[str, ...],
) -> Proposal:
    return Proposal(
        topic=topic,
        slot_id=str(slot),
        slug=slug,
        title=title,
        public_api=public_api,
        contract=contract,
        starter_design=(
            "A coherent C++17 scaffold exposes part of the declared API but "
            "omits or misimplements the task-specific mechanism."
        ),
        target_design=(
            "Complete whole-file replacements implement the exact API with "
            "warning-clean, deterministic, portable C++17 behavior."
        ),
        oracle_design=(
            "Public API and isolated-header probes plus deterministic examples, "
            "boundary assertions, a diagnosed failure mutation, and a distinct "
            "compiling semantic mutation."
        ),
        solution_strategy=strategy,
        edge_cases=edge_cases,
        mechanism=strategy,
    )


PROPOSALS: tuple[Proposal, ...] = (
    # Clock: arithmetic, state, scheduling, signal, and ordering mechanisms.
    p("Clock", 1, "pulse-coincidence-crt", "Pulse Coincidence CRT",
      "namespace pulse_coincidence { std::optional<std::int64_t> first_alignment(std::int64_t a_period, std::int64_t a_phase, std::int64_t b_period, std::int64_t b_phase, std::int64_t limit); }",
      "Return the earliest nonnegative time no greater than limit at which two periodic pulse trains fire, or nullopt when their congruences are incompatible.",
      "Use extended Euclid and a generalized Chinese-remainder merge with checked 64-bit arithmetic.",
      ("zero or negative periods are invalid", "non-coprime compatible phases", "alignment exactly at the limit")),
    p("Clock", 2, "tariff-band-shift-split", "Tariff-Band Shift Split",
      "namespace tariff_clock { struct Band { int begin_minute; int end_minute; int rate; }; std::vector<std::int64_t> split_cost(int start_minute, int duration, const std::vector<Band>& bands); }",
      "Split a possibly multi-day shift into repeating daily tariff bands and return charged minute-cost for each band in declaration order.",
      "Sweep day-boundary and band-boundary events while consuming duration without minute-by-minute simulation.",
      ("shift starts at midnight", "duration spans several days", "bands must exactly partition a day")),
    p("Clock", 3, "pauseable-countdown-ledger", "Pauseable Countdown Ledger",
      "namespace countdown_ledger { enum class OpKind { advance, pause, resume }; struct Op { OpKind kind; std::int64_t amount; }; std::int64_t remaining(std::int64_t initial, const std::vector<Op>& ops); }",
      "Replay advances and pause/resume transitions; elapsed time reduces the countdown only while running and never below zero.",
      "Implement an explicit lifecycle state machine with checked transition validation and saturating consumption.",
      ("double pause and double resume are invalid", "advance while paused", "advance past zero")),
    p("Clock", 4, "ntp-sample-consensus", "NTP Sample Consensus",
      "namespace ntp_consensus { struct Sample { std::int64_t t1,t2,t3,t4; }; struct Estimate { double offset; std::int64_t delay; }; std::optional<Estimate> estimate(const std::vector<Sample>& samples); }",
      "Discard invalid timestamp quadruples, select the minimum-delay quartile, and return the median offset with deterministic even-size averaging.",
      "Compute NTP delay/offset pairs, use selection rather than sorting all fields together, and apply a median rule.",
      ("no valid samples", "negative network delay", "even selected population")),
    p("Clock", 5, "metronome-rational-merge", "Rational Metronome Merge",
      "namespace metronome_merge { struct Beat { std::int64_t numerator; std::int64_t denominator; int source; }; std::vector<Beat> merge(std::int64_t horizon_num, std::int64_t horizon_den, const std::vector<std::pair<std::int64_t,std::int64_t>>& periods); }",
      "Merge exact rational beat times from several metronomes through a rational horizon, coalescing simultaneous beats by smallest source ID.",
      "Use a gcd-normalized rational min-heap and overflow-checked cross multiplication.",
      ("equal beats from several sources", "fractional horizon", "nonpositive period rejected")),
    p("Clock", 6, "itinerary-utc-monotonicity", "Itinerary UTC Monotonicity",
      "namespace itinerary_clock { struct Leg { std::int64_t local_departure; int departure_offset; std::int64_t local_arrival; int arrival_offset; }; std::optional<std::int64_t> minimum_layover(const std::vector<Leg>& legs); }",
      "Convert each local endpoint with its explicit UTC offset, reject time-travel legs or overlaps, and return the smallest layover.",
      "Normalize endpoints with checked subtraction and perform a single ordered itinerary validation pass.",
      ("single leg has no layover", "offset crosses a date boundary", "arrival equals next departure")),
    p("Clock", 7, "cooldown-alarm-filter", "Cooldown Alarm Filter",
      "namespace cooldown_alarm { std::vector<std::int64_t> accepted(const std::vector<std::int64_t>& requested, std::int64_t cooldown, std::int64_t reset_gap); }",
      "Accept ordered alarm requests subject to a cooldown; a sufficiently large idle gap resets the suppression history.",
      "Scan timestamp runs with two thresholds and preserve stable request order.",
      ("duplicate timestamps", "cooldown zero", "reset boundary equality")),
    p("Clock", 8, "watermark-reorder-buffer", "Watermark Reorder Buffer",
      "namespace watermark_clock { struct Event { std::int64_t timestamp; int sequence; }; std::vector<Event> release(const std::vector<Event>& arrivals, std::int64_t lateness); }",
      "Release events in timestamp/sequence order once the maximum observed timestamp establishes a watermark; flush the remainder at end of stream.",
      "Maintain a min-heap and monotone watermark while preserving deterministic tie order.",
      ("late event older than watermark", "equal timestamps", "negative lateness rejected")),
    p("Clock", 9, "skew-segment-calibration", "Skew Segment Calibration",
      "namespace skew_clock { struct Pair { std::int64_t reference; std::int64_t local; }; struct Segment { std::size_t begin; std::size_t end; double slope; double intercept; }; std::vector<Segment> calibrate(const std::vector<Pair>& points, double residual_limit); }",
      "Partition ordered clock samples into maximal segments whose least-squares affine fit stays within a residual limit.",
      "Grow segments with online regression sums and close before the first violating point.",
      ("two-point segment", "identical reference coordinates invalid", "residual exactly at limit")),
    p("Clock", 10, "vector-clock-frontier", "Vector Clock Frontier",
      "namespace vector_frontier { using Stamp = std::vector<std::uint64_t>; std::vector<std::size_t> maximal_events(const std::vector<Stamp>& events); }",
      "Return indices of causally maximal vector-clock events, retaining incomparable events and rejecting inconsistent dimensions.",
      "Apply componentwise partial-order dominance with an antichain frontier.",
      ("equal stamps keep earliest only", "all events form a chain", "incomparable events")),
    p("Clock", 11, "angular-hand-encounters", "Angular Hand Encounters",
      "namespace hand_encounters { std::vector<double> times(double hour_angle, double minute_angle, double hour_rate, double minute_rate, double horizon); }",
      "Return all times in a closed horizon when two continuously rotating hands have equal normalized angle.",
      "Solve a linear congruence over real angular displacement and enumerate the bounded integer winding range.",
      ("equal rates and equal angles", "equal rates and different angles", "encounter at horizon endpoints")),
    p("Clock", 12, "sla-business-budget", "SLA Business Budget",
      "namespace sla_budget { struct Window { std::int64_t begin; std::int64_t end; }; std::optional<std::int64_t> deadline(std::int64_t start, std::int64_t budget, const std::vector<Window>& service); }",
      "Consume a work budget only inside sorted service windows and return the exact deadline, rejecting overlaps and insufficient capacity.",
      "Validate disjoint intervals, binary-search the start window, then consume interval capacity.",
      ("start inside a gap", "zero budget", "deadline at a window end")),
    p("Clock", 13, "jitter-cluster-centers", "Jitter Cluster Centers",
      "namespace jitter_clock { std::vector<std::int64_t> centers(std::vector<std::int64_t> ticks, std::int64_t tolerance); }",
      "Cluster tick observations whose adjacent sorted gaps are within tolerance and return each cluster's lower median.",
      "Sort timestamps, form single-linkage runs, and select deterministic lower medians.",
      ("negative tolerance rejected", "bridge-connected cluster", "even cluster size")),
    p("Clock", 14, "phase-locked-loop-trace", "Phase-Locked Loop Trace",
      "namespace pll_trace { struct State { std::int64_t phase; std::int64_t frequency; }; std::vector<State> replay(State initial, const std::vector<std::int64_t>& errors, std::int64_t phase_gain, std::int64_t frequency_gain, std::int64_t modulus); }",
      "Replay an integer phase-locked loop with modular phase normalization and frequency correction after each signed phase error.",
      "Use ordered state updates with Euclidean modulo and checked multiply-add operations.",
      ("negative phase error", "modulus one", "overflowing update rejected")),
    p("Clock", 15, "temporal-quorum-window", "Temporal Quorum Window",
      "namespace temporal_quorum { struct Vote { int member; std::int64_t time; }; std::optional<std::pair<std::int64_t,std::int64_t>> shortest_window(const std::vector<Vote>& votes, int members, int quorum); }",
      "Find the shortest timestamp interval containing votes from at least quorum distinct members, breaking ties by earlier start then end.",
      "Sort votes and use a distinct-member sliding window with multiplicity counts.",
      ("repeated member votes", "quorum one", "impossible quorum")),

    # Complex Numbers: algebra, geometry, numerics, sequences, and signal mechanisms.
    p("Complex Numbers", 1, "stable-quadratic-pair", "Stable Quadratic Pair",
      "namespace stable_quadratic { std::pair<std::complex<double>,std::complex<double>> roots(double a, double b, double c); }",
      "Return both roots of a real-coefficient quadratic using a cancellation-resistant formulation and deterministic ordering.",
      "Use a complex discriminant, choose the sign maximizing denominator magnitude, and derive the second root by Vieta.",
      ("a is zero invalid", "double root", "negative discriminant")),
    p("Complex Numbers", 2, "hermitian-symmetry-audit", "Hermitian Symmetry Audit",
      "namespace hermitian_audit { struct Mismatch { std::size_t left; std::size_t right; double error; }; std::vector<Mismatch> audit(const std::vector<std::complex<double>>& spectrum, double tolerance); }",
      "Report conjugate-symmetry violations in a discrete spectrum without reporting either pair twice.",
      "Pair mirrored bins, handle DC/Nyquist self-bins, and compare with scaled tolerance.",
      ("empty spectrum", "odd and even lengths", "non-real self bin")),
    p("Complex Numbers", 3, "gaussian-integer-gcd", "Gaussian Integer GCD",
      "namespace gaussian_gcd { struct Gaussian { std::int64_t real; std::int64_t imag; }; Gaussian gcd(Gaussian a, Gaussian b); }",
      "Compute a canonical greatest common divisor in the Gaussian integers using nearest-lattice Euclidean division.",
      "Perform Gaussian Euclid with exact integer remainders and normalize the final unit associate.",
      ("both operands zero", "ties in nearest quotient", "unit normalization")),
    p("Complex Numbers", 4, "branch-continuous-log", "Branch-Continuous Log",
      "namespace branch_log { std::vector<std::complex<double>> continuous_log(const std::vector<std::complex<double>>& path); }",
      "Return logarithms along a nonzero complex path while unwrapping argument to minimize adjacent phase jumps.",
      "Compute magnitude logs and choose successive argument lifts by nearest multiple of two pi.",
      ("zero sample invalid", "cross negative real axis", "exact pi tie")),
    p("Complex Numbers", 5, "complex-two-by-two-solve", "Complex Two-by-Two Solve",
      "namespace complex_linear2 { struct Solution { std::complex<double> x; std::complex<double> y; double residual; }; std::optional<Solution> solve(std::array<std::complex<double>,4> a, std::array<std::complex<double>,2> b, double epsilon); }",
      "Solve a complex 2x2 linear system with scaled pivoting and return a residual certificate, or nullopt when numerically singular.",
      "Use scaled partial pivoting, elimination, back substitution, and an infinity-norm residual.",
      ("row swap required", "near-singular threshold", "zero row")),
    p("Complex Numbers", 6, "barycentric-complex-interpolation", "Barycentric Complex Interpolation",
      "namespace complex_barycentric { std::complex<double> interpolate(const std::vector<std::complex<double>>& nodes, const std::vector<std::complex<double>>& values, std::complex<double> query); }",
      "Evaluate the unique interpolation polynomial through distinct complex nodes using first-form barycentric weights.",
      "Build product weights, return exact node values on equality, and evaluate the rational barycentric quotient.",
      ("duplicate nodes invalid", "query equals node", "empty input invalid")),
    p("Complex Numbers", 7, "phase-unwrapping-dp", "Phase Unwrapping DP",
      "namespace phase_dp { std::vector<double> unwrap(const std::vector<double>& wrapped, double jump_penalty, int max_winding_step); }",
      "Choose integer windings for wrapped phases that minimize squared adjacent change plus winding-change penalty.",
      "Run dynamic programming over bounded winding deltas with lexicographic tie reconstruction.",
      ("empty sequence", "multiple optimal paths", "negative penalty invalid")),
    p("Complex Numbers", 8, "complex-reflection-chain", "Complex Reflection Chain",
      "namespace reflection_chain { struct Mirror { std::complex<double> point; std::complex<double> direction; }; std::complex<double> apply(std::complex<double> value, const std::vector<Mirror>& mirrors); }",
      "Reflect a point successively across oriented lines represented by a point and nonzero complex direction.",
      "Normalize each direction and apply conjugation in the line's local coordinate frame.",
      ("zero direction invalid", "point on mirror", "ordered reflections do not commute")),
    p("Complex Numbers", 9, "newton-basin-label", "Newton Basin Label",
      "namespace newton_basin { struct Result { int root_index; int iterations; std::complex<double> final_value; }; Result classify(const std::vector<std::complex<double>>& coefficients, std::complex<double> start, int max_iterations, double tolerance); }",
      "Apply Newton iteration to a complex polynomial and label convergence to the closest discovered root candidate deterministically.",
      "Evaluate polynomial and derivative together with Horner recurrence and stop on residual or singular derivative.",
      ("constant polynomial invalid", "zero derivative before convergence", "iteration limit")),
    p("Complex Numbers", 10, "complex-covariance-eigenpair", "Complex Covariance Eigenpair",
      "namespace covariance2 { struct Eigenpair { double value; std::array<std::complex<double>,2> vector; }; Eigenpair principal(const std::vector<std::array<std::complex<double>,2>>& samples); }",
      "Form a centered 2x2 Hermitian covariance matrix and return its principal eigenpair with a canonical vector phase.",
      "Accumulate Hermitian covariance, solve its analytic characteristic equation, and normalize eigenvector phase.",
      ("fewer than two samples invalid", "repeated eigenvalue", "zero first component phase")),
    p("Complex Numbers", 11, "integer-complex-power", "Integer Complex Power",
      "namespace integer_power { std::complex<double> powi(std::complex<double> base, std::int64_t exponent); }",
      "Raise a complex base to any signed 64-bit integer exponent with logarithmic multiplication count.",
      "Use exponentiation by squaring with unsigned-magnitude conversion safe for INT64_MIN.",
      ("zero to negative exponent invalid", "INT64_MIN exponent", "zero exponent")),
    p("Complex Numbers", 12, "complex-polygon-winding", "Complex Polygon Winding",
      "namespace complex_winding { int winding_number(const std::vector<std::complex<double>>& polygon, std::complex<double> query); }",
      "Return the signed winding number of a closed polygonal chain around a query, rejecting a query on the boundary.",
      "Accumulate robust oriented ray crossings with half-open endpoint rules.",
      ("self-intersecting polygon", "query on vertex", "clockwise orientation")),
    p("Complex Numbers", 13, "biquad-frequency-extrema", "Biquad Frequency Extrema",
      "namespace biquad_extrema { struct Coefficients { double b0,b1,b2,a1,a2; }; std::pair<double,double> sampled_extrema(Coefficients c, std::size_t samples); }",
      "Sample a digital biquad response on the closed Nyquist interval and return minimum and maximum magnitudes, rejecting poles on sampled points.",
      "Evaluate numerator and denominator with unit-circle complex powers and stable magnitude comparison.",
      ("samples below two invalid", "zero denominator", "ties retain earliest sample")),
    p("Complex Numbers", 14, "root-of-unity-permutation", "Root-of-Unity Permutation",
      "namespace unity_permutation { std::vector<std::size_t> nearest_bins(const std::vector<std::complex<double>>& values, std::size_t order); }",
      "Assign each nonzero sample to a distinct nearest root of unity with minimum total squared distance.",
      "Build a cost matrix and solve minimum assignment with bitmask dynamic programming and lexicographic ties.",
      ("more values than roots", "zero sample invalid", "equal-cost assignment")),
    p("Complex Numbers", 15, "complex-continued-fraction", "Complex Continued Fraction",
      "namespace complex_cf { struct Gaussian { std::int64_t real; std::int64_t imag; }; std::vector<Gaussian> expand(std::complex<double> value, std::size_t terms, double epsilon); }",
      "Expand a complex number into nearest-Gaussian-integer continued-fraction terms until the remainder is small or the term limit is reached.",
      "Round to the nearest lattice point with deterministic ties, invert the remainder, and detect termination.",
      ("nonfinite input invalid", "exact Gaussian integer", "rounding tie")),

    # Spiral Matrix: spiral order is a secondary representation; core algorithms differ.
    p("Spiral Matrix", 1, "spiral-cyclic-pattern-search", "Spiral Cyclic Pattern Search",
      "namespace spiral_pattern { std::vector<std::size_t> cyclic_matches(const std::vector<std::vector<int>>& grid, const std::vector<int>& pattern); }",
      "Read the grid in a documented inward boundary order, treat the resulting sequence cyclically, and return all match starts without materializing repeated text.",
      "Extract one permutation, build a KMP prefix table, and scan at most n+m-1 cyclic positions.",
      ("empty pattern", "pattern longer than traversal", "rectangular grid")),
    p("Spiral Matrix", 2, "spiral-permutation-cycles", "Spiral Permutation Cycles",
      "namespace spiral_cycles { std::vector<std::vector<std::size_t>> cycles(std::size_t rows, std::size_t cols); }",
      "Return the nontrivial cycles of the permutation mapping row-major positions to inward boundary-order positions.",
      "Construct inverse position mapping and decompose the permutation with visited-state traversal.",
      ("zero dimension", "fixed points omitted", "cycle rotated to smallest member")),
    p("Spiral Matrix", 3, "spiral-run-codec", "Spiral Run Codec",
      "namespace spiral_rle { struct Run { int value; std::size_t length; }; std::vector<Run> encode(const std::vector<std::vector<int>>& grid); std::vector<std::vector<int>> decode(std::size_t rows, std::size_t cols, const std::vector<Run>& runs); }",
      "Run-length encode values in boundary order and exactly reconstruct the rectangular matrix from valid runs.",
      "Share a coordinate iterator between streaming encode and validated decode while keeping codec invariants explicit.",
      ("adjacent equal runs invalid on decode", "run total mismatch", "empty dimensions")),
    p("Spiral Matrix", 4, "spiral-prefix-index", "Spiral Prefix Index",
      "namespace spiral_prefix { class Index { public: explicit Index(std::vector<std::vector<std::int64_t>> grid); std::int64_t range_sum(std::size_t first, std::size_t last) const; void update(std::size_t row, std::size_t col, std::int64_t value); }; }",
      "Support point updates and inclusive sums over boundary-order positions of a fixed rectangular grid.",
      "Build coordinate-to-rank mapping and a Fenwick tree over traversal positions.",
      ("reversed range invalid", "single-cell matrix", "checked update coordinates")),
    p("Spiral Matrix", 5, "spiral-window-median", "Spiral Window Median",
      "namespace spiral_median { std::vector<int> medians(const std::vector<std::vector<int>>& grid, std::size_t width); }",
      "Return lower medians of every fixed-width window over the inward boundary-order sequence.",
      "Use coordinate extraction plus two multisets with lazy-independent balanced rebalancing.",
      ("width zero invalid", "width larger than cells", "duplicate values")),
    p("Spiral Matrix", 6, "spiral-turn-cost-route", "Spiral Turn-Cost Route",
      "namespace spiral_route { std::optional<std::int64_t> minimum_cost(const std::vector<std::vector<int>>& blocked, int straight_cost, int turn_cost); }",
      "Find a minimum-cost route from top-left to the central cell where direction changes have a separate cost and blocked cells are forbidden.",
      "Run Dijkstra on cell-plus-heading states with deterministic neighbor order.",
      ("blocked endpoints", "even grid has documented lower-right center", "zero turn cost")),
    p("Spiral Matrix", 7, "spiral-layer-seam", "Spiral Layer Seam",
      "namespace spiral_seam { std::vector<std::pair<std::size_t,std::size_t>> minimum_seam(const std::vector<std::vector<int>>& cost); }",
      "Choose one cell from each rectangular boundary layer, requiring consecutive choices to share a row or column, with minimum total cost.",
      "Enumerate each layer perimeter and run dynamic programming across compatible layer states.",
      ("single layer", "negative costs", "lexicographic tie path")),
    p("Spiral Matrix", 8, "spiral-orientation-inference", "Spiral Orientation Inference",
      "namespace spiral_inference { struct Orientation { int corner; bool clockwise; std::size_t shift; }; std::optional<Orientation> infer(const std::vector<std::vector<int>>& grid, const std::vector<int>& observed); }",
      "Infer the unique corner, direction, and cyclic shift whose boundary traversal equals an observed full sequence.",
      "Generate the eight traversal bases and use linear-time rotation matching, rejecting ambiguity.",
      ("repeated values cause ambiguity", "one-cell grid", "observed size mismatch")),
    p("Spiral Matrix", 9, "spiral-corruption-locator", "Spiral Corruption Locator",
      "namespace spiral_corruption { std::optional<std::pair<std::size_t,std::size_t>> locate(const std::vector<std::vector<std::int64_t>>& grid, std::int64_t first, std::int64_t delta); }",
      "Assume boundary-order values should form an arithmetic progression and return the unique mismatching coordinate, or nullopt when none or multiple mismatch.",
      "Stream coordinates while generating expected terms with overflow checks and uniqueness tracking.",
      ("overflowing progression invalid", "zero delta", "multiple corrupt cells")),
    p("Spiral Matrix", 10, "spiral-hash-accumulator", "Spiral Hash Accumulator",
      "namespace spiral_hash { std::uint64_t digest(const std::vector<std::vector<std::uint32_t>>& grid, std::uint64_t base); }",
      "Compute a polynomial hash of boundary-order values using unsigned wraparound and a position-dependent direction marker.",
      "Traverse without flattening and update a specified 64-bit modular recurrence.",
      ("base zero", "empty grid has fixed seed", "rectangular single row")),
    p("Spiral Matrix", 11, "spiral-block-transpose", "Spiral Block Transpose",
      "namespace spiral_blocks { std::vector<std::vector<int>> transpose_blocks(const std::vector<std::vector<int>>& grid, std::size_t block); }",
      "Partition the boundary-order sequence into fixed blocks, transpose the ragged block table, and place the result back through the same coordinate order.",
      "Use explicit ragged block indexing and a stable column-major gather before coordinate scatter.",
      ("block zero invalid", "last block short", "empty grid")),
    p("Spiral Matrix", 12, "spiral-motion-collisions", "Spiral Motion Collisions",
      "namespace spiral_motion { struct Walker { std::size_t position; int velocity; }; std::vector<std::pair<std::size_t,std::size_t>> collisions(std::size_t rows, std::size_t cols, std::vector<Walker> walkers, std::size_t steps); }",
      "Move walkers on the cyclic boundary-order index ring and report first-step pair collisions, including edge swaps.",
      "Update modular indices synchronously and detect vertex and swap collisions with pair maps.",
      ("negative velocity", "one-cell ring", "several walkers collide together")),
    p("Spiral Matrix", 13, "spiral-region-adjacency", "Spiral Region Adjacency",
      "namespace spiral_regions { std::vector<std::vector<int>> adjacency(const std::vector<std::vector<int>>& labels); }",
      "Number equal-valued four-connected regions by first boundary-order encounter and return their sorted undirected adjacency lists.",
      "Flood-fill components, assign order-derived IDs, then scan grid edges to build a simple graph.",
      ("disconnected equal labels", "single region", "deterministic adjacency order")),
    p("Spiral Matrix", 14, "spiral-inversion-count", "Spiral Inversion Count",
      "namespace spiral_inversions { std::uint64_t count(const std::vector<std::vector<int>>& grid); }",
      "Count strict inversions in the boundary-order value sequence while treating equal values as non-inversions.",
      "Coordinate-compress values and use a Fenwick frequency tree with 64-bit count accumulation.",
      ("all equal", "descending sequence", "empty grid")),
    p("Spiral Matrix", 15, "spiral-palindrome-partition", "Spiral Palindrome Partition",
      "namespace spiral_palindrome { std::vector<std::pair<std::size_t,std::size_t>> minimum_partition(const std::vector<std::vector<char>>& grid); }",
      "Partition the boundary-order character sequence into the fewest palindromic ranges, breaking ties lexicographically by endpoints.",
      "Precompute palindrome intervals and run suffix dynamic programming with deterministic reconstruction.",
      ("empty sequence", "multiple minimum partitions", "single-character ranges")),

    # Zebra Puzzle: constraint programming mechanisms that are not one shared solver template.
    p("Zebra Puzzle", 1, "ac3-domain-reducer", "AC-3 Domain Reducer",
      "namespace ac3_reducer { struct Arc { int left; int right; std::vector<std::pair<int,int>> allowed; }; std::optional<std::vector<std::vector<int>>> reduce(std::vector<std::vector<int>> domains, const std::vector<Arc>& arcs); }",
      "Enforce binary arc consistency to a fixed point and return reduced sorted domains or nullopt on contradiction.",
      "Run an AC-3 queue with reverse-neighbor re-enqueueing and explicit support checks.",
      ("duplicate domain values normalized", "self arc", "empty domain contradiction")),
    p("Zebra Puzzle", 2, "hall-set-pruner", "Hall-Set Pruner",
      "namespace hall_pruner { std::optional<std::vector<std::vector<int>>> prune(std::vector<std::vector<int>> domains); }",
      "Apply all-different Hall-set pruning for every nonempty variable subset and detect impossible domain unions.",
      "Enumerate variable subsets with bitmasks, compare union cardinality, and remove tight-set values elsewhere.",
      ("more than twenty variables invalid", "singleton propagation", "Hall violation")),
    p("Zebra Puzzle", 3, "watched-clue-propagation", "Watched Clue Propagation",
      "namespace watched_clues { struct Literal { int variable; int value; bool equal; }; struct Clause { std::vector<Literal> literals; }; std::optional<std::vector<int>> propagate(int variables, const std::vector<Clause>& clauses, std::vector<int> assignment); }",
      "Perform unit propagation over finite-domain equality/inequality clue clauses using two watched literals per clause.",
      "Maintain watch lists, evaluate three-valued literals, move watches, and force the last viable literal.",
      ("empty clause contradiction", "already satisfied clause", "conflicting forced assignments")),
    p("Zebra Puzzle", 4, "exact-cover-dlx", "Exact Cover DLX",
      "namespace exact_cover { std::optional<std::vector<int>> lexicographic_solution(const std::vector<std::vector<int>>& rows, int columns); }",
      "Return the lexicographically smallest row-index set covering every column exactly once.",
      "Implement dancing-links cover/uncover search with smallest-column choice and lexicographic solution comparison.",
      ("uncovered column", "empty exact cover", "duplicate column in row invalid")),
    p("Zebra Puzzle", 5, "clue-entailment-check", "Clue Entailment Check",
      "namespace clue_entailment { struct Constraint { int left; int right; int relation; }; enum class Verdict { entailed, contradicted, undecided }; Verdict check(int entities, const std::vector<Constraint>& base, Constraint query); }",
      "Classify a query relation across all permutations satisfying the base clues.",
      "Backtrack with incremental relation pruning and stop once both query truth values are witnessed.",
      ("inconsistent base is invalid", "query true in every solution", "multiple solution witnesses")),
    p("Zebra Puzzle", 6, "minimal-unique-clue-set", "Minimal Unique Clue Set",
      "namespace minimal_clues { std::vector<std::size_t> select(int entities, const std::vector<std::vector<int>>& clue_solution_masks); }",
      "Choose the smallest lexicographic clue-index subset whose mask intersection leaves exactly one candidate solution.",
      "Use branch-and-bound subset search with suffix intersection lower bounds.",
      ("no unique subset", "empty set already unique", "equal-size alternatives")),
    p("Zebra Puzzle", 7, "soft-clue-maxsat", "Soft Clue MaxSAT",
      "namespace soft_clues { struct Soft { std::uint64_t satisfying_assignments; int weight; }; struct Result { int assignment; std::int64_t score; }; Result maximize(int assignment_count, const std::vector<Soft>& clues); }",
      "Select the assignment maximizing total satisfied clue weight, with smallest assignment index on ties.",
      "Accumulate weights over bitset-encoded assignment membership with checked score arithmetic.",
      ("negative weight invalid", "more than sixty-four assignments", "all scores tie")),
    p("Zebra Puzzle", 8, "symmetry-orbit-canonicalizer", "Symmetry Orbit Canonicalizer",
      "namespace symmetry_orbit { std::vector<int> canonical(std::vector<int> assignment, const std::vector<std::vector<int>>& generators); }",
      "Return the lexicographically smallest assignment reachable under permutations generated by supplied relabelings.",
      "Breadth-first traverse the finite permutation orbit with visited hashing and generator composition.",
      ("invalid generator permutation", "identity-only group", "nontrivial orbit")),
    p("Zebra Puzzle", 9, "rollback-constraint-session", "Rollback Constraint Session",
      "namespace rollback_csp { struct Command { int kind; int variable; int value; }; std::vector<std::size_t> domain_sizes(int variables, int values, const std::vector<Command>& commands); }",
      "Replay assign, forbid, checkpoint, and rollback commands and report total domain size after every command.",
      "Use a reversible change log with checkpoint stack and contradiction-preserving transactional commands.",
      ("rollback without checkpoint invalid", "forbid last value rejects command", "nested checkpoints")),
    p("Zebra Puzzle", 10, "nogood-learning-search", "Nogood Learning Search",
      "namespace nogood_search { struct BinaryBan { int a_var,a_val,b_var,b_val; }; std::optional<std::vector<int>> solve(int variables, int values, const std::vector<BinaryBan>& bans); }",
      "Find the lexicographically smallest assignment satisfying all binary bans while learning one nogood from every dead end.",
      "Use depth-first assignment, forward checking, and cached partial-assignment nogoods.",
      ("no solution", "self-variable ban", "learned nogood reuse")),
    p("Zebra Puzzle", 11, "explanation-dag", "Propagation Explanation DAG",
      "namespace explanation_dag { struct Implication { int premise; int conclusion; }; std::vector<int> shortest_explanation(int facts, const std::vector<int>& given, const std::vector<Implication>& rules, int target); }",
      "Return the smallest-cardinality sorted set of given facts that derives a target through unary implications.",
      "Condense implication SCCs, propagate bitset explanations, and compare cardinality then lexicographic order.",
      ("target underived", "target already given", "cycles in implication graph")),
    p("Zebra Puzzle", 12, "treewidth-clue-count", "Treewidth Clue Count",
      "namespace clue_tree_dp { struct EdgeRule { int parent; int child; std::vector<std::pair<int,int>> allowed; }; std::uint64_t count(int variables, int values, const std::vector<EdgeRule>& forest); }",
      "Count assignments for a forest-shaped binary clue graph with per-edge allowed value pairs.",
      "Root each tree and perform bottom-up value-indexed dynamic programming with checked addition/multiplication.",
      ("cycle rejected", "isolated variable", "count overflow rejected")),
    p("Zebra Puzzle", 13, "kth-lexicographic-solution", "K-th Lexicographic Solution",
      "namespace kth_solution { struct Ban { int variable; int value; }; std::optional<std::vector<int>> kth(int variables, int values, const std::vector<Ban>& bans, std::uint64_t index); }",
      "Return the zero-based k-th lexicographic injective assignment respecting unary bans.",
      "Use subset dynamic-programming completion counts to unrank choices without enumerating earlier solutions.",
      ("index out of range", "more variables than values", "saturated count handling")),
    p("Zebra Puzzle", 14, "weighted-clue-diagnosis", "Weighted Clue Diagnosis",
      "namespace clue_diagnosis { struct Clue { std::uint64_t mask; int removal_cost; }; std::vector<std::size_t> remove_for_consistency(int assignments, const std::vector<Clue>& clues); }",
      "Remove a minimum-cost lexicographic set of clues so at least one candidate assignment remains.",
      "Run branch-and-bound over conflicting clue intersections with admissible remaining-cost bounds.",
      ("already consistent", "equal-cost diagnoses", "zero assignments invalid")),
    p("Zebra Puzzle", 15, "constraint-order-optimizer", "Constraint Order Optimizer",
      "namespace clue_order { std::vector<std::size_t> greedy_order(std::uint64_t initial_candidates, const std::vector<std::uint64_t>& clue_masks); }",
      "Order clues by greatest immediate candidate elimination, breaking ties by smallest clue index, and stop once no clue changes the set.",
      "Maintain a candidate bitset and repeatedly choose the maximum marginal reduction.",
      ("initial candidate set empty invalid", "redundant clues omitted", "ties deterministic")),
)


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def atomic_write(path: Path, value: Any) -> None:
    data = canonical(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        Path(temporary_name).unlink(missing_ok=True)


def build_plan(batch_receipt: dict[str, Any], batch_receipt_sha256: str) -> dict[str, Any]:
    if len(PROPOSALS) != TASK_COUNT:
        raise ValueError(f"expected {TASK_COUNT} proposals, got {len(PROPOSALS)}")
    topic_slots = {(row.topic, row.slot_id) for row in PROPOSALS}
    expected_slots = {(topic, str(slot)) for topic in TOPICS for slot in range(1, 16)}
    if topic_slots != expected_slots:
        raise ValueError("proposal set does not cover 15 slots for every topic")
    if len({row.slug for row in PROPOSALS}) != TASK_COUNT:
        raise ValueError("proposal slugs are not unique")
    batch_code = batch_receipt["generation_batch_code"]
    rows: list[dict[str, Any]] = []
    for proposal in PROPOSALS:
        task_id = f"charm-ft60-{batch_code}-{proposal.slug}"
        payload = {
            **asdict(proposal),
            "edge_cases": list(proposal.edge_cases),
            "task_id": task_id,
            "generation_batch_code": batch_code,
            "generation_batch_created_at_utc": batch_receipt["generation_batch_created_at_utc"],
            "batch_code_reservation_receipt_sha256": batch_receipt_sha256,
        }
        payload["proposal_sha256"] = sha256_bytes(canonical(payload))
        rows.append(payload)
    return {
        "schema_version": "charm-v1-proposal-plan-v1",
        "protocol_id": PROTOCOL_ID,
        "generation_batch_id": batch_receipt["generation_batch_id"],
        "generation_session_id": batch_receipt["generation_session_id"],
        "generation_batch_code": batch_code,
        "generation_batch_created_at_utc": batch_receipt["generation_batch_created_at_utc"],
        "batch_code_reservation_receipt_sha256": batch_receipt_sha256,
        "topics": list(TOPICS),
        "tasks_per_topic": TASKS_PER_TOPIC,
        "authorized_task_count": TASK_COUNT,
        "scope_label": "explicit-four-topic-60-task-narrow-experiment",
        "proposals": rows,
    }


def build_curriculum(plan: dict[str, Any]) -> dict[str, Any]:
    ids = [row["task_id"] for row in plan["proposals"]]
    return {
        "schema_version": "charm-four-topic-60-curriculum-v3",
        "protocol_id": PROTOCOL_ID,
        "generation_batch_id": plan["generation_batch_id"],
        "generation_session_id": plan["generation_session_id"],
        "generation_batch_code": plan["generation_batch_code"],
        "generation_batch_created_at_utc": plan["generation_batch_created_at_utc"],
        "batch_code_reservation_receipt_sha256": plan["batch_code_reservation_receipt_sha256"],
        "proposal_plan_sha256": sha256_bytes(canonical(plan)),
        "proposals": plan["proposals"],
        "authorized_task_count": TASK_COUNT,
        "topics": list(TOPICS),
        "task_ids": ids,
        "role_counts": {"direct_verified_success": 33, "boundary_case": 12, "repair_trajectory": 12, "calibration": 3},
        "starter_counts": {"empty": 12, "skeleton": 15, "partial_implementation": 12, "semantic_bug": 9, "compile_bug": 6, "near_correct": 6},
        "editable_layout_counts": {"cpp_only": 18, "header_only": 9, "header_and_cpp": 33, "multi_file_gt2": 6},
        "header_mode_counts": {"frozen": 12, "editable": 12, "reconstructed": 12, "repaired": 12, "extended": 12},
        "api_capability_mode": "non_exclusive",
        "api_capability_minimums": {"implement_missing": 15, "preserve": 15, "extend": 15, "repair": 15, "refactor": 15},
        "api_capability_expected_counts": {"implement_missing": 39, "preserve": 60, "extend": 16, "repair": 28, "refactor": 42},
        "api_capability_assignment_rules": {
            "implement_missing": "starter is empty, skeleton, or partial_implementation",
            "preserve": "every task preserves the exact case-sensitive public API",
            "extend": "header mode is extended or the task has more than two editable files",
            "repair": "starter is semantic_bug, compile_bug, or near_correct, or role is repair_trajectory",
            "refactor": "editable layout is header_only or header_and_cpp",
        },
        "action_counts": {"empty_starter": 12, "existing_header_change": 21, "header_only_or_template": 9, "header_and_source": 12, "unparseable": 0, "unjustified_noop": 0, "action_shapes": {"source_only": 36, "header_only_or_template": 9, "header_and_source": 12, "calibration_no_change": 3}},
        "families": [{"family_id": topic, "action_topology_count": 3, "has_existing_scaffold": True} for topic in TOPICS],
        "source_counts": {"synthetic": 60},
        "required_mechanism_ids": ["public-api-completeness", "file-action-selection", "header-self-containment", "compiler-feedback-repair", "state-transition-ordering", "container-lifetime", "member-shadowing", "warning-as-error", "whole-file-application", "anchor-retention"],
        "repair_plan": {"genuine_four_turn_suffix_required": True, "failing_candidate_receipt_required": True, "corrected_candidate_receipt_required": True, "metadata_only_rows_count_as_repair": False, "planned_genuine_repair_count": 12, "repair_type_counts": {"compile_repair": 2, "linker_repair": 2, "api_repair": 2, "hidden_test_repair": 2, "runtime_repair": 2, "sanitizer_repair": 2}},
        "api_capability_counts": {"implement_missing_api": 39, "preserve_api": 60, "extend_api": 16, "repair_api": 28, "refactor_api": 42},
        "starter_type_counts": {"empty": 12, "skeleton": 15, "partial_implementation": 12, "semantic_bug": 9, "compile_bug": 6, "near_correct": 6},
        "dataset_shape_plan": {
            "histograms": {name: {"planned_rows": TASK_COUNT} for name in ("topic", "difficulty", "starter", "repair", "file_count", "header_edit", "template_usage", "exception_usage", "concurrency_usage", "pointer_usage", "ast_nodes", "api_shape")},
            "families_below_minimum": [],
        },
        "source_policy": {
            "old_tombstoned_tasks": "uniqueness-and-negative-design-evidence-only",
            "official_fixed26": "permanent-evaluation-holdout",
            "copying_allowed": False,
        },
        "canary_plan": {"authorized": False, "task_count": 20, "epochs": 5, "matched_trials": 4},
        "non_claims": ["not V1", "not SFT-ready", "not training authorization", "not benchmark uplift"],
    }


def build_dependency_preflight_plan(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "charm-ft60-dependency-preflight-plan-v1",
        "stage": "pre-generation",
        "status": "not_completed",
        "protocol_id": PROTOCOL_ID,
        "generation_batch_id": plan["generation_batch_id"],
        "task_count": TASK_COUNT,
        "cpp_standard": "c++17",
        "external_packages": [],
        "required_lanes": ["gcc", "clang", "header_isolation", "asan", "ubsan"],
        "execution_deferred_until_materialization": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-code-receipt", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    receipt = load_object(args.batch_code_receipt)
    receipt_sha = sha256_bytes(args.batch_code_receipt.read_bytes())
    if not (
        receipt.get("decision") == "PASS"
        and receipt.get("reservation_state") == "permanent"
        and receipt.get("historical_alias_only") is False
        and receipt.get("codes_reusable") is False
    ):
        raise SystemExit("batch-code receipt is not a current permanent reservation")
    plan = build_plan(receipt, receipt_sha)
    curriculum = build_curriculum(plan)
    dependency_plan = build_dependency_preflight_plan(plan)
    plan_path = args.output_dir / "proposal-plan.json"
    curriculum_path = args.output_dir / "curriculum-plan.json"
    dependency_path = args.output_dir / "dependency-preflight-plan.json"
    if plan_path.exists() or curriculum_path.exists() or dependency_path.exists():
        raise SystemExit("refusing to overwrite frozen proposal artifacts")
    atomic_write(plan_path, plan)
    atomic_write(curriculum_path, curriculum)
    atomic_write(dependency_path, dependency_plan)
    print(json.dumps({
        "proposal_plan_sha256": sha256_bytes(plan_path.read_bytes()),
        "curriculum_plan_sha256": sha256_bytes(curriculum_path.read_bytes()),
        "dependency_preflight_plan_sha256": sha256_bytes(dependency_path.read_bytes()),
        "task_count": TASK_COUNT,
        "topic_count": len(TOPICS),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
