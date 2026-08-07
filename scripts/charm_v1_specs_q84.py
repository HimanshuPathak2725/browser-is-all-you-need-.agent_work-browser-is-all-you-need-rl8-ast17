#!/usr/bin/env python3
"""Clean-room CHARM V1 task specifications for the v1r86 remediation lineage."""

from __future__ import annotations


def build_specs(Spec):
    specs = []

    budget_expressions = {
        "symptom-gap-clusters": "events.size()", "blocked-mask-run-boundaries": "samples.size()", "exposure-interval-coverage": "intervals.size()",
        "versioned-ledger-replay": "entries.size()", "largest-remainder-cents": "weights.size()", "repeated-balance-levels": "deltas.size()",
        "preorder-parent-index": "preorder.size()", "leaf-search-regions": "(insertion_keys.size()!=0U&&insertion_keys.size()>std::numeric_limits<std::size_t>::max()/insertion_keys.size()?std::numeric_limits<std::size_t>::max():insertion_keys.size()*insertion_keys.size())", "sequential-leaf-erasure": "insertion_keys.size()",
        "capacity-schedule-snapshots": "capacities.size()", "minimal-rotation-period": "values.size()", "checked-circular-window-sums": "values.size()",
        "strict-clock-field-parser": "tokens.size()", "merge-daily-availability": "windows.size()", "shortest-signed-clock-deltas": "readings.size()",
        "unit-phasor-normalization": "samples.size()", "affine-complex-chain": "steps.size()", "nearest-complex-sample": "samples.size()",
        "rail-fence-byte-encoding": "text.size()", "cyclic-xor-hex-frame": "payload.size()", "strict-run-packet-decoder": "packets.size()",
        "clockwise-diamond-perimeter": "radius>0?static_cast<std::size_t>(radius):0U", "centered-diamond-radius": "points.size()", "stable-diamond-point-filter": "points.size()",
        "weighted-course-average": "rows.size()", "attendance-eligibility": "rows.size()", "score-band-histogram": "scores.size()",
        "serpentine-plot-assignment": "children.size()", "seed-inventory-reconciliation": "requests.size()", "round-robin-buddy-pairs": "children.size()",
        "reverse-complete-owned-chunks": "values.size()", "cross-list-range-splice": "first.size()", "palindrome-mismatch-pair": "values.size()",
        "parallel-ascii-bigram-counts": "inputs.size()", "parallel-line-checksums": "lines.size()", "parallel-first-byte-location": "chunks.size()",
        "strict-dial-motion-profile": "text.size()", "extension-record-order": "records.size()", "country-route-selection": "numbers.size()",
        "rectangular-ring-cell-counts": "std::min(rows,columns)", "coordinate-spiral-rank": "rows", "counterclockwise-matrix-unwind": "matrix.size()",
        "greedy-nonoverlap-occurrences": "values.size()", "shortest-subsequence-window": "(values.size()!=0U&&values.size()>std::numeric_limits<std::size_t>::max()/values.size()?std::numeric_limits<std::size_t>::max():values.size()*values.size())", "bounded-insert-delete-distance": "first.size()",
        "target-face-reroll-indices": "dice.size()", "reroll-sum-distribution": "reroll_count", "scorecard-threshold-bonus": "scores.size()",
        "bounded-ordering-count": "labels.size()", "house-domain-propagation": "domains.size()", "perfect-house-matching-count": "left.size()",
    }

    remediation_assertions = {
        "symptom-gap-clusters": ('''auto q=cluster_symptoms_by_gap({{0,"a"},{0,"b"},{4,"c"},{8,"d"}},0);assert(q&&q->size()==3&&q->front().size()==2&&q->back().front()=="d");assert(std::accumulate(q->begin(),q->end(),std::size_t{0},[](std::size_t n,const auto& part){return n+part.size();})==4U);'''),
        "blocked-mask-run-boundaries": ('''auto q=blocked_mask_runs({0U,2U,2U,0U,1U},3U,2U);assert((q&&q->size()==1&&q->front()==std::pair<std::size_t,std::size_t>{1U,3U}));assert(std::all_of(q->begin(),q->end(),[](const auto& span){return span.first<span.second;}));'''),
        "capacity-schedule-snapshots": ('''auto q=snapshots_after_capacity_changes({4,5,6,7},4,{3,1,4});assert(q&&q->size()==3&&q->front()==std::vector<int>({5,6,7})&&q->back()==std::vector<int>({7}));assert(std::accumulate(q->begin(),q->end(),std::size_t{0},[](std::size_t n,const auto& row){return n+row.size();})==5U);'''),
        "clockwise-diamond-perimeter": ('''auto q=clockwise_diamond_perimeter(3);assert((q&&q->size()==12&&q->front()==std::pair<int,int>{0,-3}));assert(std::all_of(q->begin(),q->end(),[](const auto& point){return std::abs(point.first)+std::abs(point.second)==3;}));'''),
        "score-band-histogram": ('''auto q=score_band_histogram({10,20,30,40},{15,35});assert(q&&q->accepted==4U&&q->counts==std::vector<std::size_t>({1,2,1}));assert(std::accumulate(q->counts.begin(),q->counts.end(),std::size_t{0})==q->accepted);'''),
        "seed-inventory-reconciliation": ('''auto q=reconcile_seed_inventory({{"a",7},{"b",5}},{{"a",2},{"b",3},{"a",1}});assert((q&&*q==std::vector<std::pair<std::string,int>>({{"a",4},{"b",2}})));assert(std::all_of(q->begin(),q->end(),[](const auto& item){return !item.first.empty()&&item.second>=0;}));'''),
        "round-robin-buddy-pairs": ('''auto q=garden_buddy_pairs({"a","b","c","d","e","f"},4);assert(q&&q->size()==3);std::set<std::string> qnames;for(const auto& pair:*q){qnames.insert(pair.first);qnames.insert(pair.second);}assert(qnames.size()==6U&&qnames.count("a")==1U&&qnames.count("f")==1U);'''),
        "cross-list-range-splice": ('''auto q=splice_list_range({1,2,3},0,3,{7,8},2);assert(q&&q->first.empty()&&q->second==std::vector<int>({7,8,1,2,3}));assert(std::accumulate(q->second.begin(),q->second.end(),0)==21);'''),
        "extension-record-order": ('''auto q=order_dial_records({{"z","20","09"},{"y","10","10"},{"x","30","1"},{"w","40",""}});assert(q&&*q==std::vector<std::string>({"w","x","z","y"}));assert(std::all_of(q->begin(),q->end(),[](const auto& id){return id.size()==1U;}));'''),
        "shortest-subsequence-window": ('''auto q=shortest_subsequence_span({7,1,9,2,1,2},{1,2});assert(q&&*q&&(**q).begin==4U&&(**q).end_exclusive==6U);assert((**q).matched_length==2U);'''),
        "reroll-sum-distribution": ('''auto q=reroll_sum_distribution({2,3},2);assert(q&&q->begin()->first==7&&q->rbegin()->first==17);assert(std::accumulate(q->begin(),q->end(),std::uint64_t{0},[](std::uint64_t total,const auto& item){return total+item.second;})==36ULL);'''),
    }

    def add_budget_argument(text, name, arguments):
        needle = name + "("
        cursor = 0
        while True:
            begin = text.find(needle, cursor)
            if begin < 0:
                return text
            open_index = begin + len(name)
            depth = 0
            quote = None
            escaped = False
            close_index = None
            for index in range(open_index, len(text)):
                char = text[index]
                if quote is not None:
                    if escaped:
                        escaped = False
                    elif char == "\\":
                        escaped = True
                    elif char == quote:
                        quote = None
                    continue
                if char in "\"'":
                    quote = char
                elif char in "([{":
                    depth += 1
                elif char in ")]}":
                    depth -= 1
                    if depth == 0:
                        close_index = index
                        break
            if close_index is None:
                raise ValueError(f"unbalanced test call for {name}")
            existing = text[open_index + 1:close_index].strip()
            insertion = (", " if existing else "") + arguments
            text = text[:close_index] + insertion + text[close_index:]
            cursor = close_index + len(insertion) + 1

    def first_function_call(text, name):
        begin = text.find(name + "(")
        if begin < 0:
            raise ValueError(f"missing test call for {name}")
        open_index = begin + len(name)
        depth = 0
        quote = None
        escaped = False
        for index in range(open_index, len(text)):
            char = text[index]
            if quote is not None:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = None
                continue
            if char in "\"'":
                quote = char
            elif char in "([{":
                depth += 1
            elif char in ")]}":
                depth -= 1
                if depth == 0:
                    return text[begin:index + 1]
        raise ValueError(f"unbalanced first test call for {name}")

    def add(topic, slug, title, contract, types, signature, body, assertions, edges, strategy):
        import re
        index = len(specs)
        if slug not in budget_expressions:
            raise ValueError(f"missing operation-budget metric: {slug}")
        if slug == "parallel-ascii-bigram-counts":
            types = "struct BigramCountSummary { std::map<std::string,std::size_t> counts; std::size_t normalized_letters; };"
            signature = "std::optional<BigramCountSummary> parallel_ascii_bigrams(const std::vector<std::string>& inputs, std::size_t worker_count)"
            body = '''if(worker_count==0)return std::nullopt;if(inputs.empty())return BigramCountSummary{};const std::size_t workers=std::min(worker_count,inputs.size());using Shard=std::pair<std::map<std::string,std::size_t>,std::size_t>;std::vector<std::future<Shard>> jobs;for(std::size_t w=0;w<workers;++w)jobs.push_back(std::async(std::launch::async,[&,w]{Shard shard;for(std::size_t i=w;i<inputs.size();i+=workers){char previous=0;for(unsigned char c:inputs[i]){char current=0;if(c>='A'&&c<='Z')current=static_cast<char>(c-'A'+'a');else if(c>='a'&&c<='z')current=static_cast<char>(c);if(current!=0){++shard.second;if(previous!=0)++shard.first[std::string{previous,current}];}previous=current;}}return shard;}));std::map<std::string,std::size_t> counts;std::size_t letters=0;for(auto& job:jobs){auto shard=job.get();letters+=shard.second;for(const auto& item:shard.first)counts[item.first]+=item.second;}return BigramCountSummary{std::move(counts),letters};'''
            assertions = '''auto r=parallel_ascii_bigrams({"Ab-c","aba"},2);assert(r&&r->counts.at("ab")==2&&r->counts.at("ba")==1&&r->counts.size()==2&&r->normalized_letters==6U);auto e=parallel_ascii_bigrams({},2);assert(e&&e->counts.empty()&&e->normalized_letters==0U);assert(!parallel_ascii_bigrams({},0));assert(parallel_ascii_bigrams({"123"},1)->normalized_letters==0U);assert(parallel_ascii_bigrams({"AA"},8)->counts.at("aa")==1);'''
            contract += " Return both the ordered bigram counts and the total number of normalized ASCII letters consumed."
            edges += "|the summary reports normalized letter cardinality"
            strategy = "partitioned local bigram maps with per-shard letter accounting and deterministic merge"
        assertions += remediation_assertions.get(slug, "")
        if slug == "centered-diamond-radius":
            signature = signature.replace("long long minimum_centered_diamond_radius", "std::optional<long long> minimum_centered_diamond_radius", 1)
        match = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(", signature)
        if match is None:
            raise ValueError(f"cannot locate function name: {signature}")
        old_name = match.group(1)
        new_name = old_name + "_under_budget"
        signature = signature[:match.start(1)] + new_name + signature[match.end(1):]
        mode = index % 3
        if mode == 0:
            parameter = "std::size_t operation_budget"
            test_arguments = "1000000U"
            guard = f"const std::size_t required_work={budget_expressions[slug]};if(operation_budget<required_work)return std::nullopt;"
            budget_contract = "operation_budget is a minimum bound on the declared principal work units"
        elif mode == 1:
            parameter = "std::uint64_t operation_budget"
            test_arguments = "1000000ULL"
            guard = f"const std::uint64_t required_work=static_cast<std::uint64_t>({budget_expressions[slug]});if(operation_budget<required_work)return std::nullopt;"
            budget_contract = "the unsigned 64-bit operation_budget must cover the declared principal work units"
        else:
            parameter = "std::size_t operation_budget, bool require_exact_budget"
            test_arguments = "1000000U, false"
            guard = f"const std::size_t required_work={budget_expressions[slug]};if(operation_budget<required_work||(require_exact_budget&&operation_budget!=required_work))return std::nullopt;"
            budget_contract = "operation_budget covers the declared principal work units, and require_exact_budget additionally forbids unused budget"
        signature = signature[:-1] + ", " + parameter + ")"
        assertions = assertions.replace(old_name, new_name)
        assertions = add_budget_argument(assertions, new_name, test_arguments)
        nominal_call = first_function_call(assertions, new_name)
        if mode == 0:
            undersized_call = nominal_call.replace("1000000U", "0U", 1)
        elif mode == 1:
            undersized_call = nominal_call.replace("1000000ULL", "0ULL", 1)
        else:
            undersized_call = nominal_call.replace("1000000U, false", "0U, false", 1)
            exact_unused_call = nominal_call.replace("1000000U, false", "1000000U, true", 1)
            assertions += f"assert(!{exact_unused_call});"
        assertions += f"assert(!{undersized_call});"
        assertions = assertions.replace("assert(", "require_case(")
        body = guard + body
        namespace = re.sub(r"[^a-z0-9]+", "_", topic.casefold()).strip("_")
        definition = f"namespace charm::v1r86::{namespace} {{\n{signature} {{ {body} }}\n}}"
        tests = f"using namespace charm::v1r86::{namespace};\nint main() {{ {assertions} return 0; }}"
        extended_slug = slug + "-budgeted"
        extended_contract = contract + " The budget is fail-closed: " + budget_contract + "."
        extended_edges = edges + "|undersized operation budgets reject before substantive work|budget semantics are part of the public API"
        extended_strategy = strategy + " with an explicit fail-closed work budget"
        specs.append(Spec(topic, extended_slug, title + " with budget", extended_contract, types, signature, definition, tests, tuple(extended_edges.split("|")), extended_strategy, (extended_slug, namespace, "clean-room-v1q84-budget-extension")))

    # Allergies clean-room family.

    add("Allergies", "symptom-gap-clusters", "Symptom gap clusters",
        "Group a time-ordered symptom stream into clusters. Every event requires a nonnegative minute and nonempty case-sensitive label; minutes must be nondecreasing and max_gap must be nonnegative. Consecutive events remain together exactly when their minute difference is at most max_gap. Return labels in event order.",
        "struct SymptomEvent { int minute; std::string label; };",
        "std::optional<std::vector<std::vector<std::string>>> cluster_symptoms_by_gap(const std::vector<SymptomEvent>& events, int max_gap)",
        '''if(max_gap<0)return std::nullopt;std::vector<std::vector<std::string>> out;for(std::size_t i=0;i<events.size();++i){if(events[i].minute<0||events[i].label.empty()||(i>0&&events[i].minute<events[i-1].minute))return std::nullopt;if(i==0||events[i].minute-events[i-1].minute>max_gap)out.push_back({});out.back().push_back(events[i].label);}return out;''',
        '''auto r=cluster_symptoms_by_gap({{1,"itch"},{3,"rash"},{9,"cough"}},3);assert(r&&r->size()==2&&r->at(0)==std::vector<std::string>({"itch","rash"}));assert(cluster_symptoms_by_gap({},0)->empty());assert(!cluster_symptoms_by_gap({{2,"x"},{1,"y"}},2));assert(!cluster_symptoms_by_gap({{0,""}},1));assert(!cluster_symptoms_by_gap({},-1));''',
        "equal minutes share a cluster|the gap boundary is inclusive|input order is authoritative|empty input is valid|malformed chronology rejects",
        "single-pass validated temporal partitioning")
    add("Allergies", "blocked-mask-run-boundaries", "Blocked mask run boundaries",
        "Find maximal half-open index runs whose samples intersect blocked_mask. blocked_mask and every sample may contain only bits from known_mask. A zero blocked mask yields no runs. Invalid domain bits reject the complete request.",
        "", "std::optional<std::vector<std::pair<std::size_t,std::size_t>>> blocked_mask_runs(const std::vector<std::uint32_t>& samples, std::uint32_t known_mask, std::uint32_t blocked_mask)",
        '''if((blocked_mask&~known_mask)!=0U)return std::nullopt;std::vector<std::pair<std::size_t,std::size_t>> out;std::optional<std::size_t> begin;for(std::size_t i=0;i<samples.size();++i){if((samples[i]&~known_mask)!=0U)return std::nullopt;const bool hit=(samples[i]&blocked_mask)!=0U;if(hit&&!begin)begin=i;if(!hit&&begin){out.emplace_back(*begin,i);begin.reset();}}if(begin)out.emplace_back(*begin,samples.size());return out;''',
        '''assert((blocked_mask_runs({0U,1U,3U,0U,2U},3U,1U).value()==std::vector<std::pair<std::size_t,std::size_t>>{{1,3}}));assert(blocked_mask_runs({},0U,0U)->empty());assert(blocked_mask_runs({1U},1U,0U)->empty());assert(!blocked_mask_runs({},1U,2U));assert(!blocked_mask_runs({4U},3U,1U));''',
        "runs are maximal|indices are half-open|zero blocking selects nothing|unknown sample bits reject|blocked bits require a known domain",
        "validated bit-domain scan with explicit run state")
    add("Allergies", "exposure-interval-coverage", "Exposure interval coverage",
        "Compute covered minutes independently for each exposure label after merging overlapping or touching half-open intervals. Labels must be nonempty and bounds satisfy 0 <= begin <= end. Zero-length intervals contribute nothing. Return positive totals in lexical label order.",
        "struct ExposureInterval { int begin; int end; std::string label; };",
        "std::optional<std::vector<std::pair<std::string,long long>>> merged_exposure_minutes(const std::vector<ExposureInterval>& intervals)",
        '''std::map<std::string,std::vector<std::pair<int,int>>> groups;for(const auto& x:intervals){if(x.label.empty()||x.begin<0||x.end<x.begin)return std::nullopt;if(x.begin!=x.end)groups[x.label].push_back({x.begin,x.end});}std::vector<std::pair<std::string,long long>> out;for(auto& item:groups){auto& spans=item.second;std::sort(spans.begin(),spans.end());int begin=spans[0].first,end=spans[0].second;long long total=0;for(std::size_t i=1;i<spans.size();++i){if(spans[i].first<=end)end=std::max(end,spans[i].second);else{total+=static_cast<long long>(end)-begin;begin=spans[i].first;end=spans[i].second;}}out.emplace_back(item.first,total+static_cast<long long>(end)-begin);}return out;''',
        '''auto r=merged_exposure_minutes({{0,5,"dust"},{3,8,"dust"},{8,10,"dust"},{1,2,"pollen"}});assert(r&&*r==(std::vector<std::pair<std::string,long long>>{{"dust",10},{"pollen",1}}));assert(merged_exposure_minutes({})->empty());assert(merged_exposure_minutes({{2,2,"x"}})->empty());assert(!merged_exposure_minutes({{-1,2,"x"}}));assert(!merged_exposure_minutes({{2,1,"x"}}));''',
        "coverage is per label|touching intervals coalesce|zero lengths disappear|labels determine output order|bounds are validated before sorting",
        "per-label interval union with duration accumulation")

    add("Bank Account", "versioned-ledger-replay", "Versioned ledger replay",
        "Replay a ledger from a nonnegative opening balance. Entries must have sequence numbers exactly 1,2,... in input order. Each signed delta must keep the balance nonnegative and within long long. Return the balance after every committed entry, excluding the opening balance.",
        "struct LedgerEntry { std::size_t sequence; long long delta; };",
        "std::optional<std::vector<long long>> replay_versioned_ledger(long long opening, const std::vector<LedgerEntry>& entries)",
        '''if(opening<0)return std::nullopt;long long balance=opening;std::vector<long long> out;for(std::size_t i=0;i<entries.size();++i){if(entries[i].sequence!=i+1)return std::nullopt;const long long d=entries[i].delta;if((d>0&&balance>std::numeric_limits<long long>::max()-d)||(d<0&&balance<std::numeric_limits<long long>::min()-d))return std::nullopt;balance+=d;if(balance<0)return std::nullopt;out.push_back(balance);}return out;''',
        '''assert((replay_versioned_ledger(10,{{1,-3},{2,8}}).value()==std::vector<long long>{7,15}));assert(replay_versioned_ledger(0,{})->empty());assert(!replay_versioned_ledger(-1,{}));assert(!replay_versioned_ledger(0,{{2,1}}));assert(!replay_versioned_ledger(2,{{1,-3}}));''',
        "sequence numbering starts at one|no commit may overdraw|overflow rejects|empty history is valid|output records committed states",
        "transactional checked fold over a contiguous sequence ledger")
    add("Bank Account", "largest-remainder-cents", "Largest remainder cent allocation",
        "Allocate total_cents proportionally across nonnegative integer weights with the largest-remainder method. total_cents and the sum of weights are each bounded by one billion. At least one weight must be positive. Residual cents go by descending remainder then smaller index, and the result sums exactly to total_cents.",
        "", "std::optional<std::vector<std::uint64_t>> allocate_cents_largest_remainder(std::uint64_t total_cents, const std::vector<std::uint64_t>& weights)",
        '''constexpr std::uint64_t limit=1000000000ULL;if(total_cents>limit||weights.empty())return std::nullopt;std::uint64_t sum=0;for(auto w:weights){if(w>limit||sum>limit-w)return std::nullopt;sum+=w;}if(sum==0)return std::nullopt;std::vector<std::uint64_t> out(weights.size());std::vector<std::pair<std::uint64_t,std::size_t>> order;std::uint64_t used=0;for(std::size_t i=0;i<weights.size();++i){const std::uint64_t product=total_cents*weights[i];out[i]=product/sum;used+=out[i];order.emplace_back(product%sum,i);}std::sort(order.begin(),order.end(),[](const auto& a,const auto& b){return a.first!=b.first?a.first>b.first:a.second<b.second;});for(std::uint64_t i=0;i<total_cents-used;++i)++out[order[static_cast<std::size_t>(i)].second];return out;''',
        '''assert((allocate_cents_largest_remainder(10,{1,1,1}).value()==std::vector<std::uint64_t>{4,3,3}));assert((allocate_cents_largest_remainder(0,{2,3}).value()==std::vector<std::uint64_t>{0,0}));assert(!allocate_cents_largest_remainder(1,{}));assert(!allocate_cents_largest_remainder(1,{0,0}));assert(!allocate_cents_largest_remainder(1000000001ULL,{1}));''',
        "allocation is exact|ties favor smaller indices|zero total is supported|all-zero weights reject|declared arithmetic bounds are enforced",
        "bounded quotient-remainder allocation with deterministic residual ranking")
    add("Bank Account", "repeated-balance-levels", "Repeated balance levels",
        "Starting from a nonnegative opening balance, apply signed deltas with checked arithmetic and forbid negative intermediate balances. Count the opening balance and every resulting balance. Return balances visited at least twice as balance-count pairs ordered by increasing balance.",
        "", "std::optional<std::vector<std::pair<long long,std::size_t>>> repeated_balance_levels(long long opening, const std::vector<long long>& deltas)",
        '''if(opening<0)return std::nullopt;std::map<long long,std::size_t> counts;long long balance=opening;++counts[balance];for(long long d:deltas){if((d>0&&balance>std::numeric_limits<long long>::max()-d)||(d<0&&balance<std::numeric_limits<long long>::min()-d))return std::nullopt;balance+=d;if(balance<0)return std::nullopt;++counts[balance];}std::vector<std::pair<long long,std::size_t>> out;for(const auto& item:counts)if(item.second>=2)out.push_back(item);return out;''',
        '''assert((repeated_balance_levels(5,{2,-2,0}).value()==std::vector<std::pair<long long,std::size_t>>{{5,3}}));assert(repeated_balance_levels(0,{})->empty());assert(!repeated_balance_levels(-1,{}));assert(!repeated_balance_levels(1,{-2}));assert(repeated_balance_levels(2,{1})->empty());''',
        "the opening state is counted|zero deltas repeat a level|negative states reject|overflow rejects|output follows numeric balance order",
        "checked state walk with ordered visit cardinalities")

    add("Binary Search Tree", "preorder-parent-index", "Preorder parent index",
        "Validate a distinct-key preorder traversal of a strict integer binary-search tree and return each node's parent preorder index. The root has an empty optional. Reject duplicate keys or any key that violates a completed ancestor's lower bound.",
        "", "std::optional<std::vector<std::optional<std::size_t>>> preorder_parent_indices(const std::vector<int>& preorder)",
        '''std::vector<std::optional<std::size_t>> out(preorder.size());std::vector<std::size_t> stack;long long lower=std::numeric_limits<long long>::min();std::set<int> seen;for(std::size_t i=0;i<preorder.size();++i){const int key=preorder[i];if(static_cast<long long>(key)<=lower||!seen.insert(key).second)return std::nullopt;std::optional<std::size_t> parent;if(!stack.empty())parent=stack.back();while(!stack.empty()&&key>preorder[stack.back()]){lower=preorder[stack.back()];parent=stack.back();stack.pop_back();}out[i]=parent;stack.push_back(i);}return out;''',
        '''auto r=preorder_parent_indices({8,5,1,7,10});assert(r&&!r->at(0)&&r->at(1)==0U&&r->at(2)==1U&&r->at(3)==1U&&r->at(4)==0U);assert(preorder_parent_indices({})->empty());assert(!preorder_parent_indices({8,10,5}));assert(!preorder_parent_indices({1,1}));assert(preorder_parent_indices({2,1,3})->size()==3);''',
        "root parent is empty|keys are distinct|completed lower bounds persist|left and right parents differ|empty preorder is valid",
        "monotone ancestor stack with persistent lower-bound validation")
    add("Binary Search Tree", "leaf-search-regions", "Leaf search regions",
        "Insert at most 4096 distinct integer keys into a strict binary-search tree. Return one record for every leaf, ordered by leaf key. Each record contains the leaf key, its optional exclusive lower and upper search bounds inherited from ancestors, and its root-zero depth. Empty input is valid; duplicate keys reject the request.",
        "struct LeafSearchRegion { int leaf_key; std::optional<int> lower_exclusive; std::optional<int> upper_exclusive; std::size_t depth; };",
        "std::optional<std::vector<LeafSearchRegion>> leaf_search_regions(const std::vector<int>& insertion_keys)",
        '''if(insertion_keys.size()>4096U)return std::nullopt;struct Node{int key;int left=-1;int right=-1;};std::vector<Node> nodes;for(int key:insertion_keys){if(nodes.empty()){nodes.push_back({key,-1,-1});continue;}int current=0;while(true){Node& node=nodes[static_cast<std::size_t>(current)];if(key==node.key)return std::nullopt;int& next=key<node.key?node.left:node.right;if(next<0){next=static_cast<int>(nodes.size());nodes.push_back({key,-1,-1});break;}current=next;}}if(nodes.empty())return std::vector<LeafSearchRegion>{};struct Frame{int index;std::optional<int> low;std::optional<int> high;std::size_t depth;};std::vector<Frame> stack{{0,std::nullopt,std::nullopt,0U}};std::vector<LeafSearchRegion> out;while(!stack.empty()){Frame frame=stack.back();stack.pop_back();const Node& node=nodes[static_cast<std::size_t>(frame.index)];if(node.left<0&&node.right<0){out.push_back({node.key,frame.low,frame.high,frame.depth});continue;}if(node.right>=0)stack.push_back({node.right,node.key,frame.high,frame.depth+1U});if(node.left>=0)stack.push_back({node.left,frame.low,node.key,frame.depth+1U});}std::sort(out.begin(),out.end(),[](const LeafSearchRegion& first,const LeafSearchRegion& second){return first.leaf_key<second.leaf_key;});return out;''',
        '''auto r=leaf_search_regions({8,4,2,6,12,10});assert(r&&r->size()==3U);assert(r->at(0).leaf_key==2&&!r->at(0).lower_exclusive&&r->at(0).upper_exclusive==4&&r->at(0).depth==2U);assert(r->at(1).leaf_key==6&&r->at(1).lower_exclusive==4&&r->at(1).upper_exclusive==8);assert(r->at(2).leaf_key==10&&r->at(2).lower_exclusive==8&&r->at(2).upper_exclusive==12);assert(leaf_search_regions({})->empty());assert(!leaf_search_regions({1,1}));''',
        "leaf records follow key order|ancestor bounds are exclusive|missing outer bounds stay empty|depth is root zero|duplicates and oversize inputs reject",
        "owned indexed-node insertion followed by bound-carrying leaf frontier traversal")
    add("Binary Search Tree", "sequential-leaf-erasure", "Sequential leaf erasure",
        "Insert distinct integer keys into a BST, then erase requested keys in order. Every requested key must currently exist and be a leaf at its erasure step. Inputs are limited to 4096 keys. Return final inorder keys; any duplicate insertion or invalid erasure rejects the whole request.",
        "", "std::optional<std::vector<int>> erase_bst_leaves(const std::vector<int>& insertion_keys, const std::vector<int>& erase_keys)",
        '''if(insertion_keys.size()>4096)return std::nullopt;struct Node{int key;int left=-1;int right=-1;int parent=-1;};std::vector<Node> nodes;std::map<int,int> index;int root=-1;for(int key:insertion_keys){if(index.count(key))return std::nullopt;int parent=-1;bool attach_left=false;int current=root;while(current>=0){parent=current;attach_left=key<nodes[static_cast<std::size_t>(current)].key;current=attach_left?nodes[static_cast<std::size_t>(current)].left:nodes[static_cast<std::size_t>(current)].right;}const int here=static_cast<int>(nodes.size());nodes.push_back({key,-1,-1,parent});index[key]=here;if(parent<0)root=here;else if(attach_left)nodes[static_cast<std::size_t>(parent)].left=here;else nodes[static_cast<std::size_t>(parent)].right=here;}for(int key:erase_keys){auto found=index.find(key);if(found==index.end())return std::nullopt;Node& node=nodes[static_cast<std::size_t>(found->second)];if(node.left>=0||node.right>=0)return std::nullopt;if(node.parent<0)root=-1;else{Node& parent=nodes[static_cast<std::size_t>(node.parent)];if(parent.left==found->second)parent.left=-1;else if(parent.right==found->second)parent.right=-1;else return std::nullopt;}index.erase(found);}std::vector<int> out;std::vector<int> stack;int current=root;while(current>=0||!stack.empty()){while(current>=0){stack.push_back(current);current=nodes[static_cast<std::size_t>(current)].left;}current=stack.back();stack.pop_back();out.push_back(nodes[static_cast<std::size_t>(current)].key);current=nodes[static_cast<std::size_t>(current)].right;}return out;''',
        '''assert((erase_bst_leaves({4,2,6,1,3},{1,3,2}).value()==std::vector<int>{4,6}));assert(erase_bst_leaves({},{})->empty());assert(!erase_bst_leaves({1,1},{}));assert(!erase_bst_leaves({2,1,3},{2}));assert(!erase_bst_leaves({1},{2}));''',
        "erasure order changes validity|only current leaves may be removed|duplicate insertions reject|empty trees are supported|final traversal is sorted",
        "index-backed iterative tree construction and stepwise leaf detachment")


    add("Circular Buffer", "capacity-schedule-snapshots", "Capacity schedule snapshots",
        "Apply a sequence of capacity changes to an initial logical queue. The initial capacity must hold all initial values. After each new capacity, repeatedly discard the oldest value until the queue fits, then record that logical snapshot. Capacity zero is allowed and clears the queue.",
        "", "std::optional<std::vector<std::vector<int>>> snapshots_after_capacity_changes(const std::vector<int>& initial, std::size_t initial_capacity, const std::vector<std::size_t>& capacities)",
        '''if(initial.size()>initial_capacity)return std::nullopt;std::deque<int> queue(initial.begin(),initial.end());std::vector<std::vector<int>> out;for(std::size_t capacity:capacities){while(queue.size()>capacity)queue.pop_front();out.emplace_back(queue.begin(),queue.end());}return out;''',
        '''auto r=snapshots_after_capacity_changes({1,2,3},3,{2,5,0});assert(r&&r->at(0)==std::vector<int>({2,3})&&r->at(1)==std::vector<int>({2,3})&&r->at(2).empty());assert(snapshots_after_capacity_changes({},0,{})->empty());assert(!snapshots_after_capacity_changes({1},0,{}));assert(snapshots_after_capacity_changes({1},1,{1})->at(0)==std::vector<int>({1}));assert(snapshots_after_capacity_changes({1,2},2,{1})->at(0)==std::vector<int>({2}));''',
        "oldest values are discarded first|growth never invents values|zero capacity clears|one snapshot corresponds to each change|initial fit is validated",
        "deque-backed shrink-only capacity transitions with snapshot capture")
    add("Circular Buffer", "minimal-rotation-period", "Minimal rotation period",
        "Return the smallest positive left rotation that leaves an integer ring unchanged. Empty input returns zero, and a nonempty aperiodic ring returns its full size. Inputs longer than 4096 reject so the quadratic comparison bound is explicit.",
        "", "std::optional<std::size_t> minimal_rotation_period(const std::vector<int>& values)",
        '''if(values.size()>4096)return std::nullopt;if(values.empty())return 0U;for(std::size_t shift=1;shift<=values.size();++shift){bool same=true;for(std::size_t i=0;i<values.size();++i)if(values[i]!=values[(i+shift)%values.size()]){same=false;break;}if(same)return shift;}return std::nullopt;''',
        '''assert(minimal_rotation_period({1,2,1,2})==2U);assert(minimal_rotation_period({1,2,3})==3U);assert(minimal_rotation_period({7})==1U);assert(minimal_rotation_period({})==0U);assert(minimal_rotation_period({5,5,5})==1U);''',
        "empty period is zero|period is positive for nonempty input|aperiodic rings use full size|the first valid shift wins|work is explicitly bounded",
        "bounded cyclic equality search over candidate shifts")
    add("Circular Buffer", "checked-circular-window-sums", "Checked circular window sums",
        "For every start index, sum exactly width consecutive elements of a nonempty integer ring with wraparound. width must be from one through ring size. Detect signed long-long overflow and return one sum per start in index order.",
        "", "std::optional<std::vector<long long>> circular_window_sums(const std::vector<long long>& values, std::size_t width)",
        '''if(values.empty()||width==0||width>values.size())return std::nullopt;std::vector<long long> out;for(std::size_t start=0;start<values.size();++start){long long sum=0;for(std::size_t offset=0;offset<width;++offset){const long long x=values[(start+offset)%values.size()];if((x>0&&sum>std::numeric_limits<long long>::max()-x)||(x<0&&sum<std::numeric_limits<long long>::min()-x))return std::nullopt;sum+=x;}out.push_back(sum);}return out;''',
        '''assert((circular_window_sums({1,2,3},2).value()==std::vector<long long>{3,5,4}));assert(circular_window_sums({7},1)->at(0)==7);assert(!circular_window_sums({},1));assert(!circular_window_sums({1},0));assert(!circular_window_sums({std::numeric_limits<long long>::max(),1},2));''',
        "every start is represented|windows wrap at the end|width is closed-bounded|signed overflow rejects|output order follows starts",
        "nested bounded ring traversal with checked accumulation")

    add("Clock", "strict-clock-field-parser", "Strict clock field parser",
        "Parse each token as exactly five ASCII bytes HH:MM in 24-hour time. Digits are required at the four numeric positions, hours range 00-23, and minutes range 00-59. Return minutes since midnight in token order; one malformed token rejects all.",
        "", "std::optional<std::vector<int>> parse_clock_fields(const std::vector<std::string>& tokens)",
        '''std::vector<int> out;for(const auto& token:tokens){if(token.size()!=5||token[2]!=':'||token[0]<'0'||token[0]>'9'||token[1]<'0'||token[1]>'9'||token[3]<'0'||token[3]>'9'||token[4]<'0'||token[4]>'9')return std::nullopt;const int hour=(token[0]-'0')*10+(token[1]-'0');const int minute=(token[3]-'0')*10+(token[4]-'0');if(hour>=24||minute>=60)return std::nullopt;out.push_back(hour*60+minute);}return out;''',
        '''assert((parse_clock_fields({"00:00","23:59","07:05"}).value()==std::vector<int>{0,1439,425}));assert(parse_clock_fields({})->empty());assert(!parse_clock_fields({"7:05"}));assert(!parse_clock_fields({"24:00"}));assert(!parse_clock_fields({"12-30"}));''',
        "field width is exact|the separator position is fixed|only ASCII digits count|upper time bounds reject|input order is preserved",
        "fixed-position byte parsing with closed range checks")
    add("Clock", "merge-daily-availability", "Merge daily availability",
        "Merge non-wrapping half-open minute windows within one day. Every bound must lie in 0..1440 with begin <= end. Empty windows disappear; overlapping or touching windows coalesce. Return disjoint windows ordered by begin.",
        "struct MinuteWindow { int begin; int end; };",
        "std::optional<std::vector<MinuteWindow>> merge_daily_windows(const std::vector<MinuteWindow>& windows)",
        '''std::vector<MinuteWindow> sorted;for(auto w:windows){if(w.begin<0||w.begin>1440||w.end<0||w.end>1440||w.begin>w.end)return std::nullopt;if(w.begin!=w.end)sorted.push_back(w);}std::sort(sorted.begin(),sorted.end(),[](auto a,auto b){return a.begin!=b.begin?a.begin<b.begin:a.end<b.end;});std::vector<MinuteWindow> out;for(auto w:sorted){if(out.empty()||w.begin>out.back().end)out.push_back(w);else out.back().end=std::max(out.back().end,w.end);}return out;''',
        '''auto r=merge_daily_windows({{60,120},{100,180},{180,200},{0,0}});assert(r&&r->size()==1&&r->at(0).begin==60&&r->at(0).end==200);assert(merge_daily_windows({})->empty());assert(!merge_daily_windows({{-1,2}}));assert(!merge_daily_windows({{3,2}}));assert(!merge_daily_windows({{0,1441}}));''',
        "daily bounds include 1440 only as an end|empty windows vanish|touching windows merge|sorting is deterministic|wraparound windows are invalid",
        "validated interval sort followed by stable union")
    add("Clock", "shortest-signed-clock-deltas", "Shortest signed clock deltas",
        "Given normalized minute readings, return the shortest signed delta from each reading to the next on a 24-hour clock. Deltas lie in [-719,720]; an exact twelve-hour tie is +720. Invalid readings reject, and fewer than two readings yield an empty result.",
        "", "std::optional<std::vector<int>> shortest_clock_deltas(const std::vector<int>& readings)",
        '''for(int value:readings)if(value<0||value>=1440)return std::nullopt;std::vector<int> out;for(std::size_t i=1;i<readings.size();++i){int delta=(readings[i]-readings[i-1]+1440)%1440;if(delta>720)delta-=1440;out.push_back(delta);}return out;''',
        '''assert((shortest_clock_deltas({1380,30,750,0}).value()==std::vector<int>{90,720,690}));assert(shortest_clock_deltas({})->empty());assert(shortest_clock_deltas({5})->empty());assert(!shortest_clock_deltas({-1,0}));assert(!shortest_clock_deltas({0,1440}));''',
        "readings are normalized inputs|forward wrap may be shortest|backward travel may be shortest|twelve-hour ties are positive|adjacent pairs define output",
        "modular adjacent difference with an explicit tie convention")

    add("Complex Numbers", "unit-phasor-normalization", "Unit phasor normalization",
        "Normalize every finite nonzero complex sample to unit magnitude and return the normalized samples. Empty input is valid. A zero sample, non-finite component, non-finite magnitude, or non-finite normalized result rejects the entire vector.",
        "", "std::optional<std::vector<std::complex<double>>> normalize_unit_phasors(const std::vector<std::complex<double>>& samples)",
        '''std::vector<std::complex<double>> out;for(auto z:samples){if(!std::isfinite(z.real())||!std::isfinite(z.imag()))return std::nullopt;const double magnitude=std::hypot(z.real(),z.imag());if(magnitude==0.0||!std::isfinite(magnitude))return std::nullopt;auto value=z/magnitude;if(!std::isfinite(value.real())||!std::isfinite(value.imag()))return std::nullopt;out.push_back(value);}return out;''',
        '''using C=std::complex<double>;auto r=normalize_unit_phasors({C{3,4},C{0,-2}});assert(r&&std::abs(r->at(0)-C{0.6,0.8})<1e-12&&r->at(1)==C(0,-1));assert(normalize_unit_phasors({})->empty());assert(!normalize_unit_phasors({C{0,0}}));assert(!normalize_unit_phasors({C{std::numeric_limits<double>::infinity(),0}}));assert(normalize_unit_phasors({C{1,0}})->at(0)==C(1,0));''',
        "normalization is per sample|zero magnitude rejects|components must be finite|empty input is preserved|the result has unit magnitude",
        "hypotenuse-scaled finite phasor projection")
    add("Complex Numbers", "affine-complex-chain", "Affine complex chain",
        "Apply an ordered chain of affine complex steps z = multiplier*z + offset. The initial value and every step component must be finite, and each intermediate result must remain finite. Return the initial value when there are no steps.",
        "struct AffineStep { std::complex<double> multiplier; std::complex<double> offset; };",
        "std::optional<std::complex<double>> apply_affine_complex_chain(std::complex<double> initial, const std::vector<AffineStep>& steps)",
        '''auto finite=[](std::complex<double> z){return std::isfinite(z.real())&&std::isfinite(z.imag());};if(!finite(initial))return std::nullopt;auto value=initial;for(const auto& step:steps){if(!finite(step.multiplier)||!finite(step.offset))return std::nullopt;value=step.multiplier*value+step.offset;if(!finite(value))return std::nullopt;}return value;''',
        '''using C=std::complex<double>;auto r=apply_affine_complex_chain(C{1,1},{{C{2,0},C{1,0}},{C{0,1},C{0,0}}});assert(r&&*r==C(-2,3));assert(apply_affine_complex_chain(C{2,3},{}).value()==C(2,3));assert(!apply_affine_complex_chain(C{std::numeric_limits<double>::quiet_NaN(),0},{}));assert(!apply_affine_complex_chain(C{1,0},{{C{std::numeric_limits<double>::infinity(),0},C{0,0}}}));assert(apply_affine_complex_chain(C{0,0},{{C{1,0},C{2,4}}}).value()==C(2,4));''',
        "step order is observable|empty chains are identity|all inputs are finite|intermediate overflow rejects|both multiplier and offset are used",
        "finite-guarded left fold of affine transformations")
    add("Complex Numbers", "nearest-complex-sample", "Nearest complex sample",
        "Return the index of the sample with minimum squared Euclidean distance to a finite target. All sample components must be finite. Ties choose the smaller index, empty samples return an empty inner optional, and non-finite distance rejects.",
        "", "std::optional<std::optional<std::size_t>> nearest_complex_sample(const std::vector<std::complex<double>>& samples, std::complex<double> target)",
        '''auto finite=[](std::complex<double> z){return std::isfinite(z.real())&&std::isfinite(z.imag());};if(!finite(target))return std::nullopt;std::optional<std::size_t> best;long double distance=0;for(std::size_t i=0;i<samples.size();++i){if(!finite(samples[i]))return std::nullopt;const long double dr=static_cast<long double>(samples[i].real())-target.real(),di=static_cast<long double>(samples[i].imag())-target.imag();const long double current=dr*dr+di*di;if(!std::isfinite(current))return std::nullopt;if(!best||current<distance){best=i;distance=current;}}return best;''',
        '''using C=std::complex<double>;auto r=nearest_complex_sample({C{0,0},C{2,0},C{1,1}},C{1,0});assert(r&&*r&&**r==0U);auto e=nearest_complex_sample({},C{0,0});assert(e&&!*e);assert(!nearest_complex_sample({C{0,0}},C{std::numeric_limits<double>::infinity(),0}));assert(!nearest_complex_sample({C{std::numeric_limits<double>::quiet_NaN(),0}},C{0,0}));assert(nearest_complex_sample({C{3,4}},C{0,0})->value()==0U);''',
        "outer optional reports validity|inner optional reports data presence|distance uses both components|ties retain the first index|non-finite arithmetic rejects",
        "long-double squared-distance selection with stable ties")


    add("Crypto Square", "rail-fence-byte-encoding", "Rail fence byte encoding",
        "Encode the input bytes by a zigzag rail-fence traversal and concatenate rails from top to bottom. rail_count must be from 1 through 64; one rail and empty text preserve the input. Every byte, including whitespace and zero bytes, participates unchanged.",
        "", "std::optional<std::string> rail_fence_encode_bytes(std::string_view text, std::size_t rail_count)",
        '''if(rail_count==0||rail_count>64)return std::nullopt;if(rail_count==1||text.empty())return std::string(text);std::vector<std::string> rails(rail_count);std::size_t rail=0;bool down=true;for(char byte:text){rails[rail].push_back(byte);if(rail==0)down=true;else if(rail+1==rail_count)down=false;rail=down?rail+1:rail-1;}std::string out;out.reserve(text.size());for(const auto& row:rails)out+=row;return out;''',
        '''assert(rail_fence_encode_bytes("WEAREDISCOVERED",3)=="WECRERDSOEEAIVD");assert(rail_fence_encode_bytes("abc",1)=="abc");assert(rail_fence_encode_bytes("",4)=="");assert(!rail_fence_encode_bytes("x",0));assert(!rail_fence_encode_bytes("x",65));''',
        "all bytes are retained|rail bounds are explicit|one rail is identity|zigzag endpoints reverse direction|output length equals input length",
        "bounded rail accumulation driven by a reversible zigzag cursor")
    add("Crypto Square", "cyclic-xor-hex-frame", "Cyclic XOR hex frame",
        "XOR every payload byte with a cyclic nonempty key and emit two lowercase hexadecimal digits per transformed byte. Append a colon and two hex digits for the XOR of all transformed bytes. Key length is at most 256, and output-size overflow rejects.",
        "", "std::optional<std::string> xor_hex_frame(std::string_view payload, std::string_view key)",
        '''if(key.empty()||key.size()>256||payload.size()>(std::numeric_limits<std::size_t>::max()-3U)/2U)return std::nullopt;const char* hex="0123456789abcdef";std::string out;out.reserve(payload.size()*2U+3U);unsigned char checksum=0;for(std::size_t i=0;i<payload.size();++i){const unsigned char value=static_cast<unsigned char>(payload[i])^static_cast<unsigned char>(key[i%key.size()]);checksum=static_cast<unsigned char>(checksum^value);out.push_back(hex[value>>4U]);out.push_back(hex[value&15U]);}out.push_back(':');out.push_back(hex[checksum>>4U]);out.push_back(hex[checksum&15U]);return out;''',
        '''assert(xor_hex_frame("ABC","K")=="0a0908:0b");assert(xor_hex_frame("","x")==":00");assert(!xor_hex_frame("", ""));assert(xor_hex_frame("a","a")=="00:00");assert(!xor_hex_frame("x",std::string(257,'k')));''',
        "the key cycles by payload index|hexadecimal is lowercase|checksum covers transformed bytes|empty payload has a frame|output sizing is checked",
        "cyclic byte XOR with streaming hexadecimal and parity checksum")
    add("Crypto Square", "strict-run-packet-decoder", "Strict run packet decoder",
        "Decode packets formatted as decimal_count*byte; with no separators between packets. Counts range from 1 through 999, have no leading zero, and are followed by exactly one payload byte and a semicolon. max_decoded_size must be at most 4096; reject output above that caller-supplied limit or any malformed packet.",
        "", "std::optional<std::string> decode_strict_run_packets(std::string_view packets, std::size_t max_decoded_size)",
        '''if(max_decoded_size>4096U)return std::nullopt;std::string out;std::size_t i=0;while(i<packets.size()){if(packets[i]<'1'||packets[i]>'9')return std::nullopt;std::size_t count=0;while(i<packets.size()&&packets[i]>='0'&&packets[i]<='9'){count=count*10U+static_cast<std::size_t>(packets[i]-'0');if(count>999)return std::nullopt;++i;}if(i>=packets.size()||packets[i]!='*'||i+2>=packets.size()||packets[i+2]!=';')return std::nullopt;const char value=packets[i+1];if(count>max_decoded_size||out.size()>max_decoded_size-count)return std::nullopt;out.append(count,value);i+=3;}return out;''',
        '''assert(decode_strict_run_packets("3*a;2*b;",5)=="aaabb");assert(decode_strict_run_packets("",0)=="");assert(!decode_strict_run_packets("0*a;",9));assert(!decode_strict_run_packets("2*a",9));assert(!decode_strict_run_packets("3*x;",2));assert(!decode_strict_run_packets("1*x;",4097));''',
        "counts forbid leading zero|payload is exactly one byte|every packet ends with semicolon|the caller limit is bounded and enforced|empty packet stream fits a zero limit",
        "deterministic decimal-state parsing against a validated caller budget")

    add("Diamond", "clockwise-diamond-perimeter", "Clockwise diamond perimeter",
        "Return integer coordinates on the Manhattan diamond |x|+|y|=radius in clockwise order, starting at the top point (0,-radius). radius must be 0 through 10000. Radius zero returns the origin once; positive radii return exactly 4*radius distinct points.",
        "", "std::optional<std::vector<std::pair<int,int>>> clockwise_diamond_perimeter(int radius)",
        '''if(radius<0||radius>10000)return std::nullopt;if(radius==0)return std::vector<std::pair<int,int>>{{0,0}};std::vector<std::pair<int,int>> out;out.reserve(static_cast<std::size_t>(4*radius));int x=0,y=-radius;for(int i=0;i<radius;++i){out.emplace_back(x,y);++x;++y;}for(int i=0;i<radius;++i){out.emplace_back(x,y);--x;++y;}for(int i=0;i<radius;++i){out.emplace_back(x,y);--x;--y;}for(int i=0;i<radius;++i){out.emplace_back(x,y);++x;--y;}return out;''',
        '''assert((clockwise_diamond_perimeter(1).value()==std::vector<std::pair<int,int>>{{0,-1},{1,0},{0,1},{-1,0}}));assert((clockwise_diamond_perimeter(0)->at(0)==std::pair<int,int>(0,0)));assert(clockwise_diamond_perimeter(2)->size()==8);assert(!clockwise_diamond_perimeter(-1));assert(!clockwise_diamond_perimeter(10001));''',
        "the top coordinate is first|movement is clockwise|positive radii have four equal sides|no closing duplicate is emitted|radius is allocation-bounded",
        "four directed diagonal edge walks with explicit cardinality")
    add("Diamond", "centered-diamond-radius", "Centered diamond radius",
        "Return the smallest nonnegative Manhattan radius centered at the origin that contains every integer point. Empty input has radius zero. Use wide arithmetic so INT_MIN coordinates are valid, and return a long-long radius.",
        "", "long long minimum_centered_diamond_radius(const std::vector<std::pair<int,int>>& points)",
        '''long long radius=0;for(const auto& point:points){const long long x=point.first,y=point.second;const long long distance=(x<0?-x:x)+(y<0?-y:y);radius=std::max(radius,distance);}return radius;''',
        '''assert(minimum_centered_diamond_radius({{1,2},{-4,0}})==4);assert(minimum_centered_diamond_radius({})==0);assert(minimum_centered_diamond_radius({{0,0}})==0);assert(minimum_centered_diamond_radius({{std::numeric_limits<int>::min(),0}})==2147483648LL);assert(minimum_centered_diamond_radius({{-2,-3}})==5);''',
        "empty input yields zero|both axes contribute|negative coordinates use magnitude|INT_MIN is widened before negation|the maximum point distance determines radius",
        "wide Manhattan-distance maximum over all points")
    add("Diamond", "stable-diamond-point-filter", "Stable diamond point filter",
        "Select points whose Manhattan distance from a declared integer center is at most radius. radius must be nonnegative. Compute differences in long long, preserve duplicates and input order, and return no result for an invalid radius.",
        "", "std::optional<std::vector<std::pair<int,int>>> points_inside_diamond(const std::vector<std::pair<int,int>>& points, std::pair<int,int> center, long long radius)",
        '''if(radius<0)return std::nullopt;std::vector<std::pair<int,int>> out;for(const auto& point:points){const long long dx=static_cast<long long>(point.first)-center.first,dy=static_cast<long long>(point.second)-center.second;const long long distance=(dx<0?-dx:dx)+(dy<0?-dy:dy);if(distance<=radius)out.push_back(point);}return out;''',
        '''assert((points_inside_diamond({{0,0},{2,0},{1,1},{0,0}},{0,0},2).value()==std::vector<std::pair<int,int>>{{0,0},{2,0},{1,1},{0,0}}));assert(points_inside_diamond({}, {1,1},0)->empty());assert(points_inside_diamond({{1,1}}, {0,0},1)->empty());assert(!points_inside_diamond({}, {0,0},-1));assert(points_inside_diamond({{3,4}}, {3,4},0)->size()==1);''',
        "the boundary is included|the center may be nonzero|duplicates remain|input order remains|negative radii reject",
        "stable wide-distance predicate filtering")

    add("Grade School", "weighted-course-average", "Weighted course average",
        "Compute a rounded weighted average from score-weight rows. Scores are 0 through 100 and weights are 1 through 100000. The total weight must not exceed one billion. Round to the nearest integer with exact half ties upward; empty rows reject.",
        "struct WeightedScore { int score; int weight; };", "std::optional<int> rounded_weighted_average(const std::vector<WeightedScore>& rows)",
        '''if(rows.empty())return std::nullopt;long long numerator=0,total=0;for(const auto& row:rows){if(row.score<0||row.score>100||row.weight<=0||row.weight>100000||total>1000000000LL-row.weight)return std::nullopt;total+=row.weight;numerator+=static_cast<long long>(row.score)*row.weight;}return static_cast<int>((numerator+total/2)/total);''',
        '''assert(rounded_weighted_average({{80,1},{90,3}})==88);assert(rounded_weighted_average({{80,1},{81,1}})==81);assert(!rounded_weighted_average({}));assert(!rounded_weighted_average({{101,1}}));assert(!rounded_weighted_average({{50,0}}));''',
        "scores use a closed range|weights are positive|the total weight is bounded|half ties round upward|empty coursework rejects",
        "bounded exact weighted numerator with integer half-up rounding")
    add("Grade School", "attendance-eligibility", "Attendance eligibility",
        "Validate unique nonempty student IDs with nonnegative absence and tardy counts. A student's penalty is 2*absences+tardies; return IDs whose penalty is at most max_penalty in lexical order. max_penalty must be nonnegative and arithmetic overflow rejects.",
        "struct AttendanceRow { std::string id; int absences; int tardies; };", "std::optional<std::vector<std::string>> attendance_eligible_ids(const std::vector<AttendanceRow>& rows, int max_penalty)",
        '''if(max_penalty<0)return std::nullopt;std::set<std::string> ids;std::vector<std::string> out;for(const auto& row:rows){if(row.id.empty()||row.absences<0||row.tardies<0||!ids.insert(row.id).second||row.absences>(std::numeric_limits<int>::max()-row.tardies)/2)return std::nullopt;if(row.absences*2+row.tardies<=max_penalty)out.push_back(row.id);}std::sort(out.begin(),out.end());return out;''',
        '''assert((attendance_eligible_ids({{"zoe",1,1},{"amy",0,2},{"max",2,0}},3).value()==std::vector<std::string>{"amy","zoe"}));assert(attendance_eligible_ids({},0)->empty());assert(!attendance_eligible_ids({{"",0,0}},1));assert(!attendance_eligible_ids({{"a",0,0},{"a",1,0}},2));assert(!attendance_eligible_ids({},-1));''',
        "IDs are globally unique|absences have double weight|the threshold is inclusive|output is lexical|penalty arithmetic is checked",
        "validated weighted attendance filter with deterministic ordering")
    add("Grade School", "score-band-histogram", "Score band histogram",
        "Count scores into ascending bands defined by strictly increasing cutlines from 0 through 100. Band zero contains scores below cutlines[0], and each subsequent band begins at its cutline. Return both cutlines.size()+1 counts and the number of accepted scores. Scores outside 0..100 reject.",
        "struct ScoreBandHistogram { std::vector<std::size_t> counts; std::size_t accepted; };", "std::optional<ScoreBandHistogram> score_band_histogram(const std::vector<int>& scores, const std::vector<int>& cutlines)",
        '''for(std::size_t i=0;i<cutlines.size();++i)if(cutlines[i]<0||cutlines[i]>100||(i>0&&cutlines[i]<=cutlines[i-1]))return std::nullopt;std::vector<std::size_t> counts(cutlines.size()+1);for(int score:scores){if(score<0||score>100)return std::nullopt;const auto band=std::upper_bound(cutlines.begin(),cutlines.end(),score)-cutlines.begin();++counts[static_cast<std::size_t>(band)];}return ScoreBandHistogram{std::move(counts),scores.size()};''',
        '''auto r=score_band_histogram({0,59,60,89,90,100},{60,90});assert(r&&r->counts==std::vector<std::size_t>({2,2,2})&&r->accepted==6U);auto e=score_band_histogram({},{});assert(e&&e->counts==std::vector<std::size_t>({0})&&e->accepted==0U);assert(!score_band_histogram({101},{50}));assert(!score_band_histogram({}, {50,50}));assert(score_band_histogram({50},{50})->counts.at(1)==1U);''',
        "cutlines are strictly increasing|scores equal to a cutline enter the higher band|both score endpoints are accepted|accepted equals the score cardinality|empty score input yields one zero count",
        "upper-bound classification into a validated histogram report")


    add("Kindergarten Garden", "serpentine-plot-assignment", "Serpentine plot assignment",
        "Assign unique nonempty child names to every cell of a rows-by-columns garden. Child count must equal the checked cell product. Traverse even rows left-to-right and odd rows right-to-left, returning each child with its row and column in child input order.",
        "struct PlotAssignment { std::string child; std::size_t row; std::size_t column; };", "std::optional<std::vector<PlotAssignment>> assign_serpentine_plots(std::size_t rows, std::size_t columns, const std::vector<std::string>& children)",
        '''if(rows!=0&&columns>std::numeric_limits<std::size_t>::max()/rows)return std::nullopt;if(children.size()!=rows*columns)return std::nullopt;std::set<std::string> names;std::vector<PlotAssignment> out;for(std::size_t i=0;i<children.size();++i){if(children[i].empty()||!names.insert(children[i]).second)return std::nullopt;const std::size_t row=i/columns,column=i%columns;out.push_back({children[i],row,row%2==0?column:columns-1-column});}return out;''',
        '''auto r=assign_serpentine_plots(2,3,{"a","b","c","d","e","f"});assert(r&&r->at(0).column==0&&r->at(3).column==2&&r->at(5).column==0);assert(assign_serpentine_plots(0,4,{})->empty());assert(!assign_serpentine_plots(1,2,{"a"}));assert(!assign_serpentine_plots(1,2,{"a","a"}));assert(!assign_serpentine_plots(1,1,{""}));''',
        "cell cardinality is exact|odd rows reverse direction|names are unique|zero-area gardens require no children|coordinates remain in bounds",
        "checked rectangular indexing with parity-directed columns")
    add("Kindergarten Garden", "seed-inventory-reconciliation", "Seed inventory reconciliation",
        "Reconcile nonnegative seed inventory against planting requests. Initial plant names are unique and nonempty; each request count is positive and names an existing plant. A request may not exceed remaining stock. Return all final counts in lexical plant order, atomically rejecting any invalid request.",
        "struct SeedRequest { std::string plant; int count; };", "std::optional<std::vector<std::pair<std::string,int>>> reconcile_seed_inventory(const std::vector<std::pair<std::string,int>>& inventory, const std::vector<SeedRequest>& requests)",
        '''std::map<std::string,int> stock;for(const auto& item:inventory)if(item.first.empty()||item.second<0||!stock.emplace(item).second)return std::nullopt;for(const auto& request:requests){auto it=stock.find(request.plant);if(request.count<=0||it==stock.end()||it->second<request.count)return std::nullopt;it->second-=request.count;}return std::vector<std::pair<std::string,int>>(stock.begin(),stock.end());''',
        '''auto r=reconcile_seed_inventory({{"violet",4},{"clover",3}},{{"clover",2},{"violet",1}});assert(r&&*r==(std::vector<std::pair<std::string,int>>{{"clover",1},{"violet",3}}));assert(reconcile_seed_inventory({},{})->empty());assert(!reconcile_seed_inventory({{"x",1},{"x",2}},{}));assert(!reconcile_seed_inventory({{"x",1}},{{"x",2}}));assert(!reconcile_seed_inventory({{"x",1}},{{"y",1}}));''',
        "inventory names are unique|requests are strictly positive|stock cannot go negative|all requests reference inventory|result order is lexical",
        "validated map copy with atomic decrement replay")
    add("Kindergarten Garden", "round-robin-buddy-pairs", "Round robin buddy pairs",
        "Pair an even number of at least two unique nonempty children for a zero-based round of the circle-method schedule. round must be less than child_count-1. Keep the first child fixed, rotate the remaining children, lexicalize each pair, and return pairs ordered lexically.",
        "", "std::optional<std::vector<std::pair<std::string,std::string>>> garden_buddy_pairs(const std::vector<std::string>& children, std::size_t round)",
        '''if(children.size()<2||children.size()%2!=0||round>=children.size()-1)return std::nullopt;std::set<std::string> names;for(const auto& child:children)if(child.empty()||!names.insert(child).second)return std::nullopt;std::vector<std::string> ring=children;for(std::size_t r=0;r<round;++r)std::rotate(ring.begin()+1,ring.end()-1,ring.end());std::vector<std::pair<std::string,std::string>> out;for(std::size_t i=0;i<ring.size()/2;++i){auto pair=std::make_pair(ring[i],ring[ring.size()-1-i]);if(pair.second<pair.first)std::swap(pair.first,pair.second);out.push_back(pair);}std::sort(out.begin(),out.end());return out;''',
        '''auto r=garden_buddy_pairs({"a","b","c","d"},0);assert(r&&*r==(std::vector<std::pair<std::string,std::string>>{{"a","d"},{"b","c"}}));auto s=garden_buddy_pairs({"a","b","c","d"},1);assert(s&&s->size()==2&&*s!=*r);assert(!garden_buddy_pairs({},0));assert(!garden_buddy_pairs({"a","b","c"},0));assert(!garden_buddy_pairs({"a","a"},0));''',
        "participant count is positive even|round range is closed by schedule size|the anchor child stays fixed|each child appears once per round|pair and list ordering are deterministic",
        "circle-method rotation with canonical pair projection")

    add("Linked List", "reverse-complete-owned-chunks", "Reverse complete owned chunks",
        "Build a singly linked chain with unique ownership from values. Reverse each complete block of chunk_size values, while a final incomplete block keeps its original order. chunk_size must be positive. Return the final sequence without losing or duplicating nodes.",
        "", "std::optional<std::vector<int>> reverse_complete_owned_chunks(const std::vector<int>& values, std::size_t chunk_size)",
        '''if(chunk_size==0)return std::nullopt;struct Node{int value;std::unique_ptr<Node> next;explicit Node(int x):value(x){}};std::unique_ptr<Node> head;Node* tail=nullptr;for(int value:values){auto node=std::make_unique<Node>(value);Node* raw=node.get();if(tail)tail->next=std::move(node);else head=std::move(node);tail=raw;}std::vector<int> out;for(Node* node=head.get();node;node=node->next.get())out.push_back(node->value);for(std::size_t begin=0;begin+chunk_size<=out.size();begin+=chunk_size)std::reverse(out.begin()+static_cast<std::ptrdiff_t>(begin),out.begin()+static_cast<std::ptrdiff_t>(begin+chunk_size));return out;''',
        '''assert((reverse_complete_owned_chunks({1,2,3,4,5},2).value()==std::vector<int>{2,1,4,3,5}));assert(reverse_complete_owned_chunks({},3)->empty());assert(reverse_complete_owned_chunks({1,2},3)==std::vector<int>({1,2}));assert(reverse_complete_owned_chunks({1,2},1)==std::vector<int>({1,2}));assert(!reverse_complete_owned_chunks({1},0));''',
        "chunk size is positive|only complete chunks reverse|tail order is stable|owned nodes preserve cardinality|empty input is valid",
        "unique-owned chain construction followed by bounded block projection")
    add("Linked List", "cross-list-range-splice", "Cross-list range splice",
        "Remove the half-open range [begin,end) from the first logical list and insert it before insert_index in the second list. Bounds may equal their list sizes, begin may equal end, and all indices are validated before mutation. Return both resulting sequences.",
        "struct SpliceResult { std::vector<int> first; std::vector<int> second; };", "std::optional<SpliceResult> splice_list_range(const std::vector<int>& first, std::size_t begin, std::size_t end, const std::vector<int>& second, std::size_t insert_index)",
        '''if(begin>end||end>first.size()||insert_index>second.size())return std::nullopt;SpliceResult out;out.first.insert(out.first.end(),first.begin(),first.begin()+static_cast<std::ptrdiff_t>(begin));out.first.insert(out.first.end(),first.begin()+static_cast<std::ptrdiff_t>(end),first.end());out.second.insert(out.second.end(),second.begin(),second.begin()+static_cast<std::ptrdiff_t>(insert_index));out.second.insert(out.second.end(),first.begin()+static_cast<std::ptrdiff_t>(begin),first.begin()+static_cast<std::ptrdiff_t>(end));out.second.insert(out.second.end(),second.begin()+static_cast<std::ptrdiff_t>(insert_index),second.end());return out;''',
        '''auto r=splice_list_range({1,2,3,4},1,3,{8,9},1);assert(r&&r->first==std::vector<int>({1,4})&&r->second==std::vector<int>({8,2,3,9}));auto e=splice_list_range({1},1,1,{},0);assert(e&&e->first==std::vector<int>({1})&&e->second.empty());assert(!splice_list_range({},1,1,{},0));assert(!splice_list_range({1},1,0,{},0));assert(!splice_list_range({},0,0,{},1));''',
        "ranges are half-open|empty ranges move nothing|insertion may occur at the end|all bounds validate first|relative order is preserved",
        "prevalidated dual-list range extraction and insertion")
    add("Linked List", "palindrome-mismatch-pair", "Palindrome mismatch pair",
        "Compare a logical list from both ends and return the first mismatching index pair. Pairs are examined outermost inward. A palindrome, empty list, or singleton returns an empty optional; otherwise return (left,right) for the earliest mismatch.",
        "", "std::optional<std::pair<std::size_t,std::size_t>> first_palindrome_mismatch(const std::vector<int>& values)",
        '''if(values.size()<2)return std::nullopt;for(std::size_t left=0;left<values.size()/2;++left){const std::size_t right=values.size()-1-left;if(values[left]!=values[right])return std::pair<std::size_t,std::size_t>{left,right};}return std::nullopt;''',
        '''assert((first_palindrome_mismatch({1,2,3,1})==std::pair<std::size_t,std::size_t>(1,2)));assert(!first_palindrome_mismatch({1,2,1}));assert(!first_palindrome_mismatch({}));assert(!first_palindrome_mismatch({7}));assert((first_palindrome_mismatch({1,2})==std::pair<std::size_t,std::size_t>(0,1)));''',
        "outer pairs are checked first|indices refer to original order|odd centers need no comparison|empty lists are palindromes|only the first mismatch is returned",
        "two-ended index walk with early mismatch return")

    add("Parallel Letter Frequency", "parallel-ascii-bigram-counts", "Parallel ASCII bigram counts",
        "Count adjacent lowercase ASCII-letter bigrams independently within each input string, folding uppercase ASCII to lowercase and treating every nonletter as a boundary. Use exactly min(worker_count,input_count) async shards for nonempty input. worker_count zero rejects.",
        "", "std::optional<std::map<std::string,std::size_t>> parallel_ascii_bigrams(const std::vector<std::string>& inputs, std::size_t worker_count)",
        '''if(worker_count==0)return std::nullopt;if(inputs.empty())return std::map<std::string,std::size_t>{};const std::size_t workers=std::min(worker_count,inputs.size());std::vector<std::future<std::map<std::string,std::size_t>>> jobs;for(std::size_t w=0;w<workers;++w)jobs.push_back(std::async(std::launch::async,[&,w]{std::map<std::string,std::size_t> local;for(std::size_t i=w;i<inputs.size();i+=workers){char previous=0;for(unsigned char c:inputs[i]){char current=0;if(c>='A'&&c<='Z')current=static_cast<char>(c-'A'+'a');else if(c>='a'&&c<='z')current=static_cast<char>(c);if(current!=0&&previous!=0)++local[std::string{previous,current}];previous=current;}}return local;}));std::map<std::string,std::size_t> out;for(auto& job:jobs)for(const auto& item:job.get())out[item.first]+=item.second;return out;''',
        '''auto r=parallel_ascii_bigrams({"Ab-c","aba"},2);assert(r&&r->at("ab")==2&&r->at("ba")==1&&r->size()==2);assert(parallel_ascii_bigrams({},2)->empty());assert(!parallel_ascii_bigrams({},0));assert(parallel_ascii_bigrams({"123"},1)->empty());assert(parallel_ascii_bigrams({"AA"},8)->at("aa")==1);''',
        "bigrams never cross strings|nonletters break adjacency|ASCII case folds explicitly|worker count is capped|result keys are lexical",
        "sharded boundary-aware bigram maps with ordered reduction")
    add("Parallel Letter Frequency", "parallel-line-checksums", "Parallel line checksums",
        "Compute one deterministic 64-bit FNV-1a checksum for each byte string using bounded asynchronous partitions. Every byte participates as unsigned data, output order matches input order, and worker_count zero rejects even for empty input.",
        "", "std::optional<std::vector<std::uint64_t>> parallel_line_checksums(const std::vector<std::string>& lines, std::size_t worker_count)",
        '''if(worker_count==0)return std::nullopt;std::vector<std::uint64_t> out(lines.size());if(lines.empty())return out;const std::size_t workers=std::min(worker_count,lines.size());std::vector<std::future<void>> jobs;for(std::size_t w=0;w<workers;++w)jobs.push_back(std::async(std::launch::async,[&,w]{for(std::size_t i=w;i<lines.size();i+=workers){std::uint64_t hash=1469598103934665603ULL;for(unsigned char c:lines[i]){hash^=c;hash*=1099511628211ULL;}out[i]=hash;}}));for(auto& job:jobs)job.get();return out;''',
        '''auto r=parallel_line_checksums({"","a","a"},2);assert(r&&r->size()==3&&r->at(1)==r->at(2)&&r->at(0)!=r->at(1));assert(parallel_line_checksums({},1)->empty());assert(!parallel_line_checksums({},0));assert(parallel_line_checksums({"x"},9)->size()==1);assert(parallel_line_checksums({std::string(1,'\\0')},1)->at(0)!=parallel_line_checksums({""},1)->at(0));''',
        "each output slot has one writer|all bytes affect the checksum|unsigned wrap is intentional|empty strings have the offset basis|worker count is positive",
        "disjoint async FNV scans with stable output indices")
    add("Parallel Letter Frequency", "parallel-first-byte-location", "Parallel first byte location",
        "Find the lexicographically earliest (chunk_index,byte_index) containing target after scanning chunks in async shards. worker_count must be positive. Return an empty inner optional when absent, and preserve byte identity without case folding.",
        "", "std::optional<std::optional<std::pair<std::size_t,std::size_t>>> parallel_first_byte(const std::vector<std::string>& chunks, unsigned char target, std::size_t worker_count)",
        '''if(worker_count==0)return std::nullopt;if(chunks.empty())return std::optional<std::pair<std::size_t,std::size_t>>{};const std::size_t workers=std::min(worker_count,chunks.size());std::vector<std::future<std::optional<std::pair<std::size_t,std::size_t>>>> jobs;for(std::size_t w=0;w<workers;++w)jobs.push_back(std::async(std::launch::async,[&,w]{for(std::size_t i=w;i<chunks.size();i+=workers)for(std::size_t j=0;j<chunks[i].size();++j)if(static_cast<unsigned char>(chunks[i][j])==target)return std::optional<std::pair<std::size_t,std::size_t>>{{i,j}};return std::optional<std::pair<std::size_t,std::size_t>>{};}));std::optional<std::pair<std::size_t,std::size_t>> best;for(auto& job:jobs){auto found=job.get();if(found&&(!best||*found<*best))best=found;}return best;''',
        '''auto r=parallel_first_byte({"ba","ab","a"},static_cast<unsigned char>('a'),2);assert((r&&*r&&**r==std::pair<std::size_t,std::size_t>(0,1)));auto e=parallel_first_byte({"x"},static_cast<unsigned char>('z'),1);assert(e&&!*e);assert(!parallel_first_byte({},0U,0));assert(parallel_first_byte({},0U,2)&&!*parallel_first_byte({},0U,2));assert((parallel_first_byte({"z"},static_cast<unsigned char>('z'),8)->value()==std::pair<std::size_t,std::size_t>(0,0)));''',
        "outer optional validates workers|inner optional represents absence|chunk index dominates byte index|byte comparison is exact|reduction is deterministic",
        "local earliest shard searches with ordered optional reduction")


    add("Phone Number", "strict-dial-motion-profile", "Strict dial motion profile",
        "Parse an optional leading plus followed by a telephone digit stream. Decimal digits are retained; only space, hyphen, parentheses, and dot may separate them. The normalized stream must contain 7 through 15 digits. Return the digits, the number of adjacent repeated keys, and the Manhattan travel distance across the standard telephone keypad with zero below eight.",
        "struct DialMotionProfile { std::string digits; std::size_t repeated_keys; std::size_t manhattan_distance; };",
        "std::optional<DialMotionProfile> analyze_dial_motion(std::string_view text)",
        '''std::string digits;digits.reserve(15U);for(std::size_t index=0;index<text.size();++index){const unsigned char byte=static_cast<unsigned char>(text[index]);if(byte==\'+\'){if(index!=0U)return std::nullopt;continue;}if(byte>=\'0\'&&byte<=\'9\')digits.push_back(static_cast<char>(byte));else if(byte!=\' \'&&byte!=\'-\'&&byte!=\'(\'&&byte!=\')\'&&byte!=\'.\')return std::nullopt;if(digits.size()>15U)return std::nullopt;}if(digits.size()<7U)return std::nullopt;const std::array<std::pair<int,int>,10> coordinate={{{3,1},{0,0},{0,1},{0,2},{1,0},{1,1},{1,2},{2,0},{2,1},{2,2}}};std::size_t repeats=0U;std::size_t distance=0U;for(std::size_t index=1;index<digits.size();++index){const std::size_t before=static_cast<std::size_t>(digits[index-1]-\'0\');const std::size_t after=static_cast<std::size_t>(digits[index]-\'0\');if(before==after)++repeats;distance+=static_cast<std::size_t>(std::abs(coordinate[before].first-coordinate[after].first)+std::abs(coordinate[before].second-coordinate[after].second));}return DialMotionProfile{std::move(digits),repeats,distance};''',
        '''auto r=analyze_dial_motion("+1 (202) 555-0100");assert(r&&r->digits=="12025550100"&&r->repeated_keys==3U&&r->manhattan_distance==18U);auto p=analyze_dial_motion("(212) 555.0100");assert(p&&p->digits=="2125550100");assert(!analyze_dial_motion("123"));assert(!analyze_dial_motion("12+34567"));assert(!analyze_dial_motion("CALL-NOW"));''',
        "a plus is allowed only as the first byte|separator grammar is closed|normalized length is 7 through 15|repeated adjacent digits are counted|keypad travel uses telephone coordinates",
        "closed-grammar digit extraction followed by coordinate-transition aggregation")
    add("Phone Number", "extension-record-order", "Extension record order",
        "Validate unique nonempty record IDs, nonempty digit-only national numbers, and optional digit-only extensions. Sort record IDs by numeric extension without integer conversion: empty extension first, then shorter length, then lexical digits; break ties by national number and ID.",
        "struct DialRecord { std::string id; std::string national; std::string extension; };", "std::optional<std::vector<std::string>> order_dial_records(const std::vector<DialRecord>& records)",
        '''auto digits=[](const std::string& value){return std::all_of(value.begin(),value.end(),[](unsigned char c){return c>='0'&&c<='9';});};std::set<std::string> ids;for(const auto& r:records)if(r.id.empty()||r.national.empty()||!digits(r.national)||(!r.extension.empty()&&!digits(r.extension))||!ids.insert(r.id).second)return std::nullopt;std::vector<const DialRecord*> sorted;for(const auto& r:records)sorted.push_back(&r);std::sort(sorted.begin(),sorted.end(),[](const auto* a,const auto* b){if(a->extension.empty()!=b->extension.empty())return a->extension.empty();if(a->extension.size()!=b->extension.size())return a->extension.size()<b->extension.size();if(a->extension!=b->extension)return a->extension<b->extension;if(a->national!=b->national)return a->national<b->national;return a->id<b->id;});std::vector<std::string> out;for(const auto* r:sorted)out.push_back(r->id);return out;''',
        '''assert((order_dial_records({{"c","300","12"},{"a","200",""},{"b","100","2"}}).value()==std::vector<std::string>{"a","b","c"}));assert(order_dial_records({})->empty());assert(!order_dial_records({{"","1",""}}));assert(!order_dial_records({{"a","1x",""}}));assert(!order_dial_records({{"a","1",""},{"a","2",""}}));''',
        "IDs are unique|national numbers are nonempty digits|extensions may be empty|numeric order avoids overflow|ties have two stable keys",
        "validated pointer sort using canonical digit-string magnitude order")
    add("Phone Number", "country-route-selection", "Country route selection",
        "Route normalized international numbers through the longest declared digit prefix. Each number must begin with one plus followed by 1 through 32 digits. Route prefixes are unique nonempty digit strings with nonempty labels. Return one route label per number, rejecting any unmatched number.",
        "struct CountryRoute { std::string prefix; std::string label; };", "std::optional<std::vector<std::string>> select_country_routes(const std::vector<std::string>& numbers, const std::vector<CountryRoute>& routes)",
        '''auto digits=[](std::string_view value){return std::all_of(value.begin(),value.end(),[](unsigned char c){return c>='0'&&c<='9';});};std::set<std::string> prefixes;for(const auto& route:routes)if(route.prefix.empty()||route.label.empty()||!digits(route.prefix)||!prefixes.insert(route.prefix).second)return std::nullopt;std::vector<std::string> out;for(const auto& number:numbers){if(number.size()<2||number.size()>33||number[0]!='+'||!digits(std::string_view(number).substr(1)))return std::nullopt;const CountryRoute* best=nullptr;for(const auto& route:routes)if(number.compare(1,route.prefix.size(),route.prefix)==0&&(!best||route.prefix.size()>best->prefix.size()))best=&route;if(!best)return std::nullopt;out.push_back(best->label);}return out;''',
        '''auto r=select_country_routes({"+1202555","+44123"},{{"1","north"},{"1202","dc"},{"44","uk"}});assert(r&&*r==std::vector<std::string>({"dc","uk"}));assert(select_country_routes({},{})->empty());assert(!select_country_routes({"1202"},{{"1","x"}}));assert(!select_country_routes({"+99"},{{"1","x"}}));assert(!select_country_routes({},{{"1","x"},{"1","y"}}));''',
        "international plus is mandatory|number length is bounded|prefixes are unique|longest matching prefix wins|every number must route",
        "validated route table with longest prefix selection")

    add("Spiral Matrix", "rectangular-ring-cell-counts", "Rectangular ring cell counts",
        "Return the number of cells in each concentric rectangular ring, outermost first. Zero in either dimension yields no rings. Reject rows*columns overflow. Degenerate one-row or one-column inner rings count each cell once, and all counts sum to the matrix area.",
        "", "std::optional<std::vector<std::size_t>> rectangular_ring_cell_counts(std::size_t rows, std::size_t columns)",
        '''if(rows!=0&&columns>std::numeric_limits<std::size_t>::max()/rows)return std::nullopt;std::vector<std::size_t> out;while(rows>0&&columns>0){if(rows==1)out.push_back(columns);else if(columns==1)out.push_back(rows);else out.push_back(2U*rows+2U*columns-4U);if(rows<=2||columns<=2)break;rows-=2;columns-=2;}return out;''',
        '''assert((rectangular_ring_cell_counts(3,4).value()==std::vector<std::size_t>{10,2}));assert(rectangular_ring_cell_counts(0,4)->empty());assert(rectangular_ring_cell_counts(1,3)->at(0)==3);assert((rectangular_ring_cell_counts(4,4).value()==std::vector<std::size_t>{12,4}));assert(!rectangular_ring_cell_counts(std::numeric_limits<std::size_t>::max(),2));''',
        "outer ring is first|degenerate rings do not double count|zero area has no rings|dimension product is checked|ring counts partition the area",
        "shrinking dimensions with explicit degenerate perimeter formulas")
    add("Spiral Matrix", "coordinate-spiral-rank", "Coordinate spiral rank",
        "Return the zero-based visit rank of one coordinate in the clockwise top-left spiral of a rectangle. Dimensions must have a nonzero product at most one million, and the coordinate must be in bounds. The implementation must not allocate a full coordinate path.",
        "", "std::optional<std::size_t> clockwise_spiral_rank(std::size_t rows, std::size_t columns, std::size_t target_row, std::size_t target_column)",
        '''if(rows==0||columns==0||rows>1000000U/columns||target_row>=rows||target_column>=columns)return std::nullopt;std::size_t top=0,bottom=rows-1,left=0,right=columns-1,rank=0;while(top<=bottom&&left<=right){for(std::size_t c=left;c<=right;++c,++rank)if(top==target_row&&c==target_column)return rank;if(++top>bottom)break;for(std::size_t r=top;r<=bottom;++r,++rank)if(r==target_row&&right==target_column)return rank;if(right--==0||left>right)break;for(std::size_t c=right+1;c-->left;++rank)if(bottom==target_row&&c==target_column)return rank;if(bottom--==0||top>bottom)break;for(std::size_t r=bottom+1;r-->top;++rank)if(r==target_row&&left==target_column)return rank;++left;}return std::nullopt;''',
        '''assert(clockwise_spiral_rank(2,3,0,0)==0U);assert(clockwise_spiral_rank(2,3,1,0)==5U);assert(clockwise_spiral_rank(3,3,1,1)==8U);assert(!clockwise_spiral_rank(0,3,0,0));assert(!clockwise_spiral_rank(2,2,2,0));''',
        "rank is zero based|the traversal starts top left|the coordinate must be in bounds|work is area-bounded|no path materialization is required",
        "shrinking-boundary traversal with immediate coordinate rank return")
    add("Spiral Matrix", "counterclockwise-matrix-unwind", "Counterclockwise matrix unwind",
        "Unwind a rectangular integer matrix counterclockwise from the top-left corner, moving down first. Rows must have equal width and total cells must not exceed one million. Empty outer input is valid; nonempty input may not contain zero-width rows.",
        "", "std::optional<std::vector<int>> unwind_matrix_counterclockwise(const std::vector<std::vector<int>>& matrix)",
        '''if(matrix.empty())return std::vector<int>{};const std::size_t rows=matrix.size(),columns=matrix[0].size();if(columns==0||rows>1000000U/columns)return std::nullopt;for(const auto& row:matrix)if(row.size()!=columns)return std::nullopt;std::vector<int> out;out.reserve(rows*columns);long long top=0,bottom=static_cast<long long>(rows)-1,left=0,right=static_cast<long long>(columns)-1;while(top<=bottom&&left<=right){for(long long r=top;r<=bottom;++r)out.push_back(matrix[static_cast<std::size_t>(r)][static_cast<std::size_t>(left)]);++left;if(left>right)break;for(long long c=left;c<=right;++c)out.push_back(matrix[static_cast<std::size_t>(bottom)][static_cast<std::size_t>(c)]);--bottom;if(top>bottom)break;for(long long r=bottom;r>=top;--r)out.push_back(matrix[static_cast<std::size_t>(r)][static_cast<std::size_t>(right)]);--right;if(left>right)break;for(long long c=right;c>=left;--c)out.push_back(matrix[static_cast<std::size_t>(top)][static_cast<std::size_t>(c)]);++top;}return out;''',
        '''assert((unwind_matrix_counterclockwise({{1,2,3},{4,5,6}}).value()==std::vector<int>{1,4,5,6,3,2}));assert(unwind_matrix_counterclockwise({})->empty());assert(!unwind_matrix_counterclockwise({{}}));assert(!unwind_matrix_counterclockwise({{1},{2,3}}));assert(unwind_matrix_counterclockwise({{7}})->at(0)==7);''',
        "the initial direction is downward|rectangular shape is mandatory|each cell appears exactly once|empty outer input is valid|total work is explicitly bounded",
        "four-side counterclockwise boundary contraction")

    add("Sublist", "greedy-nonoverlap-occurrences", "Greedy non-overlap occurrences",
        "Return the maximum-cardinality leftmost set of non-overlapping exact pattern occurrences in values at or after start_offset. pattern must be nonempty and start_offset may equal but not exceed values.size(). After a match resume immediately after that match; otherwise advance by one.",
        "", "std::optional<std::vector<std::size_t>> greedy_nonoverlap_positions(const std::vector<int>& values, const std::vector<int>& pattern, std::size_t start_offset)",
        '''if(pattern.empty()||start_offset>values.size())return std::nullopt;std::vector<std::size_t> out;std::size_t start=start_offset;while(pattern.size()<=values.size()-start){bool match=std::equal(pattern.begin(),pattern.end(),values.begin()+static_cast<std::ptrdiff_t>(start));if(match){out.push_back(start);start+=pattern.size();}else ++start;}return out;''',
        '''assert((greedy_nonoverlap_positions({1,1,1,1},{1,1},0).value()==std::vector<std::size_t>{0,2}));assert(greedy_nonoverlap_positions({}, {1},0)->empty());assert(!greedy_nonoverlap_positions({1},{},0));assert((greedy_nonoverlap_positions({0,1,2,1,2},{1,2},2).value()==std::vector<std::size_t>{3}));assert(greedy_nonoverlap_positions({1},{2},1)->empty());assert(!greedy_nonoverlap_positions({1},{1},2));''',
        "pattern is nonempty|the start offset is closed-bounded|matches never overlap|leftmost matches win within the suffix|positions are ascending",
        "offset-seeded greedy exact-window scan with match-sized jumps")
    add("Sublist", "shortest-subsequence-window", "Shortest subsequence window",
        "Find the shortest contiguous half-open span of values that contains pattern as an ordered subsequence. Both inputs are limited to 512 elements and pattern must be nonempty. Break equal-length ties by smaller begin index. Return an empty inner optional when no span exists; the result record also reports pattern length.",
        "struct SubsequenceSpan { std::size_t begin; std::size_t end_exclusive; std::size_t matched_length; };",
        "std::optional<std::optional<SubsequenceSpan>> shortest_subsequence_span(const std::vector<int>& values, const std::vector<int>& pattern)",
        '''if(values.size()>512U||pattern.empty()||pattern.size()>512U)return std::nullopt;std::optional<SubsequenceSpan> best;for(std::size_t start=0;start<values.size();++start){if(values[start]!=pattern.front())continue;std::size_t cursor=start;std::size_t matched=0U;while(cursor<values.size()&&matched<pattern.size()){if(values[cursor]==pattern[matched])++matched;++cursor;}if(matched!=pattern.size())continue;const SubsequenceSpan candidate{start,cursor,pattern.size()};if(!best||candidate.end_exclusive-candidate.begin<best->end_exclusive-best->begin)best=candidate;}return std::optional<std::optional<SubsequenceSpan>>{best};''',
        '''auto r=shortest_subsequence_span({9,1,4,2,3,1,2,3},{1,2,3});assert(r&&*r&&(**r).begin==5U&&(**r).end_exclusive==8U&&(**r).matched_length==3U);auto tie=shortest_subsequence_span({1,9,2,1,8,2},{1,2});assert(tie&&*tie&&(**tie).begin==0U&&(**tie).end_exclusive==3U);auto none=shortest_subsequence_span({1,2},{3});assert(none&&!*none);assert(!shortest_subsequence_span({1},{}));assert(shortest_subsequence_span({}, {1})&&!*shortest_subsequence_span({}, {1}));''',
        "spans are half open|pattern order is preserved without requiring adjacency|shorter spans dominate|equal lengths choose smaller begins|outer and inner optional states are distinct",
        "start-indexed subsequence completion with deterministic shortest-span reduction")
    add("Sublist", "bounded-insert-delete-distance", "Bounded insert-delete distance",
        "Compute the minimum number of insertions and deletions needed to transform first into second; substitution therefore costs two. Each sequence is limited to 512 elements and max_distance to 1024. Return an empty inner optional when the exact distance exceeds max_distance.",
        "", "std::optional<std::optional<std::size_t>> bounded_insert_delete_distance(const std::vector<int>& first, const std::vector<int>& second, std::size_t max_distance)",
        '''if(first.size()>512||second.size()>512||max_distance>1024)return std::nullopt;std::vector<std::size_t> previous(second.size()+1),current(second.size()+1);std::iota(previous.begin(),previous.end(),0U);for(std::size_t i=1;i<=first.size();++i){current[0]=i;for(std::size_t j=1;j<=second.size();++j)current[j]=first[i-1]==second[j-1]?previous[j-1]:1U+std::min(previous[j],current[j-1]);previous.swap(current);}if(previous.back()>max_distance)return std::optional<std::size_t>{};return std::optional<std::size_t>{previous.back()};''',
        '''auto r=bounded_insert_delete_distance({1,2,3},{1,4,3},2);assert(r&&*r&&**r==2U);auto e=bounded_insert_delete_distance({1,2,3},{},2);assert(e&&!*e);assert(bounded_insert_delete_distance({}, {},0)->value()==0U);assert(!bounded_insert_delete_distance(std::vector<int>(513),{},1));assert(!bounded_insert_delete_distance({}, {},1025));''',
        "substitution costs delete plus insert|outer optional validates bounds|inner optional reports threshold excess|empty sequences are explicit|dynamic programming is size-bounded",
        "two-row insertion-deletion dynamic program with threshold projection")


    add("Yacht", "target-face-reroll-indices", "Target face reroll indices",
        "Validate exactly five six-sided dice and a target face from 1 through 6. Return the zero-based indices of dice that do not equal the target, in ascending order. Matching dice are kept, including the case where every die matches.",
        "", "std::optional<std::vector<std::size_t>> reroll_indices_for_face(const std::array<int,5>& dice, int target_face)",
        '''if(target_face<1||target_face>6)return std::nullopt;std::vector<std::size_t> out;for(std::size_t i=0;i<dice.size();++i){if(dice[i]<1||dice[i]>6)return std::nullopt;if(dice[i]!=target_face)out.push_back(i);}return out;''',
        '''assert((reroll_indices_for_face({6,2,6,1,6},6).value()==std::vector<std::size_t>{1,3}));assert(reroll_indices_for_face({3,3,3,3,3},3)->empty());assert(!reroll_indices_for_face({1,2,3,4,7},1));assert(!reroll_indices_for_face({1,2,3,4,5},0));assert(reroll_indices_for_face({1,2,3,4,5},6)->size()==5);''',
        "all five dice are validated|target face uses the same domain|matching dice remain kept|indices are ascending|all-match output is empty",
        "single-pass validated keep-or-reroll index projection")
    add("Yacht", "reroll-sum-distribution", "Reroll sum distribution",
        "Enumerate the exact sum distribution after keeping declared dice and rolling reroll_count fair six-sided dice. Kept dice must be valid, total final dice may not exceed five, and reroll_count is at most five. Return sum-to-outcome-count pairs ordered by sum.",
        "", "std::optional<std::map<int,std::uint64_t>> reroll_sum_distribution(const std::vector<int>& kept, std::size_t reroll_count)",
        '''if(reroll_count>5||kept.size()>5-reroll_count)return std::nullopt;int base=0;for(int die:kept){if(die<1||die>6)return std::nullopt;base+=die;}std::map<int,std::uint64_t> counts;std::function<void(std::size_t,int)> visit=[&](std::size_t rolled,int sum){if(rolled==reroll_count){++counts[sum];return;}for(int face=1;face<=6;++face)visit(rolled+1,sum+face);};visit(0,base);return counts;''',
        '''auto r=reroll_sum_distribution({6},1);assert(r&&r->at(7)==1&&r->at(12)==1&&r->size()==6);auto fixed=reroll_sum_distribution({1,2,3,4,5},0);assert(fixed&&fixed->at(15)==1&&fixed->size()==1);assert(!reroll_sum_distribution({7},0));assert(!reroll_sum_distribution({1},5));assert(!reroll_sum_distribution({},6));''',
        "outcome counts are exact|sum keys are ordered|kept dice contribute to every outcome|zero rerolls has one outcome|final hand size is bounded",
        "bounded recursive Cartesian enumeration into an ordered sum histogram")
    add("Yacht", "scorecard-threshold-bonus", "Scorecard threshold bonus",
        "Aggregate unique nonempty category scores from 0 through 50. If the raw sum is at least threshold, add bonus; threshold and bonus must be nonnegative. Return raw sum, awarded bonus, and final total as long long values with checked arithmetic.",
        "struct CategoryScore { std::string category; int score; };", "std::optional<std::array<long long,3>> apply_scorecard_bonus(const std::vector<CategoryScore>& scores, long long threshold, long long bonus)",
        '''if(threshold<0||bonus<0)return std::nullopt;std::set<std::string> categories;long long raw=0;for(const auto& row:scores){if(row.category.empty()||row.score<0||row.score>50||!categories.insert(row.category).second)return std::nullopt;raw+=row.score;}const long long awarded=raw>=threshold?bonus:0;if(raw>std::numeric_limits<long long>::max()-awarded)return std::nullopt;return std::array<long long,3>{raw,awarded,raw+awarded};''',
        '''assert((apply_scorecard_bonus({{"ones",3},{"sixes",24}},25,10).value()==std::array<long long,3>{27,10,37}));assert((apply_scorecard_bonus({},0,5).value()==std::array<long long,3>{0,5,5}));assert(!apply_scorecard_bonus({{"x",1},{"x",2}},1,1));assert(!apply_scorecard_bonus({{"x",51}},1,1));assert(!apply_scorecard_bonus({},-1,0));''',
        "categories are unique|individual scores are bounded|threshold comparison is inclusive|empty scorecards can earn a zero threshold bonus|final addition is checked",
        "validated category fold with explicit threshold award state")

    add("Zebra Puzzle", "bounded-ordering-count", "Bounded ordering count",
        "Count permutations of up to nine distinct nonempty labels satisfying strict before constraints. Constraint endpoints must be known and distinct. Stop after max_solutions and report both the observed count and whether more solutions exist; max_solutions must be positive.",
        "struct BeforeConstraint { std::string before; std::string after; }; struct OrderingCount { std::size_t count; bool truncated; };", "std::optional<OrderingCount> count_bounded_orderings(const std::vector<std::string>& labels, const std::vector<BeforeConstraint>& constraints, std::size_t max_solutions)",
        '''if(labels.size()>9||max_solutions==0)return std::nullopt;std::set<std::string> domain(labels.begin(),labels.end());if(domain.size()!=labels.size()||domain.count("")!=0)return std::nullopt;for(const auto& c:constraints)if(c.before==c.after||domain.count(c.before)==0||domain.count(c.after)==0)return std::nullopt;std::vector<std::string> order(domain.begin(),domain.end());std::size_t count=0;bool truncated=false;do{std::map<std::string,std::size_t> position;for(std::size_t i=0;i<order.size();++i)position[order[i]]=i;bool valid=true;for(const auto& c:constraints)if(position[c.before]>=position[c.after]){valid=false;break;}if(valid){if(count==max_solutions){truncated=true;break;}++count;}}while(std::next_permutation(order.begin(),order.end()));return OrderingCount{count,truncated};''',
        '''auto r=count_bounded_orderings({"a","b","c"},{{"a","b"}},10);assert(r&&r->count==3&&!r->truncated);auto t=count_bounded_orderings({"a","b","c"},{},2);assert(t&&t->count==2&&t->truncated);assert(count_bounded_orderings({}, {},1)->count==1);assert(!count_bounded_orderings({"a","a"},{},1));assert(!count_bounded_orderings({"a"},{{"a","x"}},1));''',
        "label count is factorial-bounded|constraints use known distinct endpoints|count truncation is explicit|zero labels have one ordering|solution limit is positive",
        "lexical permutation enumeration with capped constraint counting")
    add("Zebra Puzzle", "house-domain-propagation", "House domain propagation",
        "Propagate fixed values through house candidate domains. Every house begins with a nonempty set of nonempty values. Fixed clues use valid distinct house indices and distinct values present in that house. Fix each clue, then repeatedly remove singleton values from other houses; reject any empty domain or duplicate singleton.",
        "struct FixedDomainValue { std::size_t house; std::string value; };", "std::optional<std::vector<std::set<std::string>>> propagate_house_domains(std::vector<std::set<std::string>> domains, const std::vector<FixedDomainValue>& fixed)",
        '''for(const auto& domain:domains)if(domain.empty()||domain.count("")!=0)return std::nullopt;std::set<std::size_t> houses;std::set<std::string> values;for(const auto& clue:fixed){if(clue.house>=domains.size()||domains[clue.house].count(clue.value)==0||!houses.insert(clue.house).second||!values.insert(clue.value).second)return std::nullopt;domains[clue.house]={clue.value};}bool changed=true;while(changed){changed=false;std::set<std::string> singles;for(const auto& domain:domains)if(domain.size()==1&&!singles.insert(*domain.begin()).second)return std::nullopt;for(auto& domain:domains)if(domain.size()>1)for(const auto& value:singles)if(domain.erase(value)){changed=true;if(domain.empty())return std::nullopt;}}return domains;''',
        '''auto r=propagate_house_domains({{"red"},{"red","blue"},{"blue","green"}},{});assert(r&&r->at(1)==std::set<std::string>({"blue"})&&r->at(2)==std::set<std::string>({"green"}));assert(propagate_house_domains({},{})->empty());assert(!propagate_house_domains({{}},{}));assert(!propagate_house_domains({{"a"},{"a"}},{}));assert(!propagate_house_domains({{"a"}},{{1,"a"}}));''',
        "domains start nonempty|fixed houses and values are unique|singletons eliminate globally|duplicate singleton assignments reject|propagation reaches a fixed point",
        "iterated singleton all-different propagation over explicit domains")
    add("Zebra Puzzle", "perfect-house-matching-count", "Perfect house matching count",
        "Count perfect bijections from left labels to right labels using an explicit allowed-pair relation. Each side contains the same number of distinct nonempty labels and is limited to eight. Allowed endpoints must be known and pairs unique. Return the exact number of perfect matchings, including one for two empty domains.",
        "struct AllowedPair { std::string left; std::string right; };", "std::optional<std::size_t> count_perfect_house_matchings(const std::vector<std::string>& left, const std::vector<std::string>& right, const std::vector<AllowedPair>& allowed)",
        '''if(left.size()!=right.size()||left.size()>8)return std::nullopt;std::set<std::string> left_set(left.begin(),left.end()),right_set(right.begin(),right.end());if(left_set.size()!=left.size()||right_set.size()!=right.size()||left_set.count("")||right_set.count(""))return std::nullopt;std::set<std::pair<std::string,std::string>> edges;for(const auto& edge:allowed)if(left_set.count(edge.left)==0||right_set.count(edge.right)==0||!edges.emplace(edge.left,edge.right).second)return std::nullopt;std::vector<std::string> assignment=right;std::sort(assignment.begin(),assignment.end());std::size_t count=0;do{bool valid=true;for(std::size_t i=0;i<left.size();++i)if(edges.count({left[i],assignment[i]})==0){valid=false;break;}if(valid)++count;}while(std::next_permutation(assignment.begin(),assignment.end()));return count;''',
        '''assert(count_perfect_house_matchings({"a","b"},{"x","y"},{{"a","x"},{"a","y"},{"b","x"},{"b","y"}})==2U);assert(count_perfect_house_matchings({}, {}, {})==1U);assert(count_perfect_house_matchings({"a"},{"x"},{{"a","x"}})==1U);assert(!count_perfect_house_matchings({"a"},{},{}));assert(!count_perfect_house_matchings({"a","a"},{"x","y"},{}));''',
        "both domains have equal size|labels are distinct and nonempty|allowed pairs are unique|empty domains have one empty bijection|matching count is exact within the bounded domain",
        "bounded right-side permutation enumeration against an allowed edge set")


    # TASK_SPECS_START

    if len(specs) != 51:
        raise ValueError(f"expected 51 clean-room specs, got {len(specs)}")
    return specs
