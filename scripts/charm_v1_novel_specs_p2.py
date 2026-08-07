#!/usr/bin/env python3
"""Second independently authored clean-room CHARM V1 specification family.

The earlier planning lineages are permanent duplicate evidence.  These 51
contracts deliberately use different observable behavior, APIs, algorithms,
edge partitions, and test oracles while retaining only the frozen topic names.
"""

from __future__ import annotations

import re


def build_specs(Spec):
    specs = []

    def add(topic, slug, title, contract, types, signature, body, tests, edges, strategy, tags):
        topic_ns = re.sub(r"[^a-z0-9]+", "_", topic.casefold()).strip("_")
        namespace = f"charm::v1p2::{topic_ns}"
        definition_signature = signature
        declared_types = re.findall(
            r"(?:struct|class|enum\s+class)\s+([A-Za-z_][A-Za-z0-9_]*)",
            types,
        )
        for type_name in declared_types:
            definition_signature = re.sub(
                rf"(?<!:)\b{re.escape(type_name)}\b",
                f"{namespace}::{type_name}",
                definition_signature,
            )
        match = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(", definition_signature)
        if match is None:
            raise ValueError(f"cannot qualify signature: {signature}")
        qualified = (definition_signature[:match.start(1)] + namespace + "::" +
                     definition_signature[match.start(1):])
        # Keep generated C++ warning-clean even when a compact owner row puts
        # several guarded statements on one source line.  Newlines inside a
        # for-header or initializer are valid C++ and preserve exact behavior.
        formatted_body = body.strip().replace(";", ";\n").replace("}", "}\n")
        definition = qualified + " {\n" + formatted_body + "\n}"
        test_source = f"using namespace {namespace};\nint main() {{\n{tests.strip()}\n    return 0;\n}}"
        specs.append(Spec(topic, slug, title, contract, types, signature, definition,
                          test_source, tuple(edges), strategy, tuple(tags)))

    add(
        "Allergies", "contraindication-dose-score", "Contraindication dose score",
        "Evaluate a meal exposure against a unique limit table. Unknown allergens are ignored; known totals above their limits contribute excess milligrams multiplied by severity. Reject negative quantities, duplicate limits, nonpositive severity, or integer overflow.",
        "struct Exposure { std::string allergen; int milligrams; };\nstruct Limit { std::string allergen; int max_milligrams; int severity; };",
        "std::optional<int> contraindication_score(const std::vector<Exposure>& exposures, const std::vector<Limit>& limits)",
        """std::map<std::string, std::pair<int,int>> table;
    for (const auto& limit : limits) {
        if (limit.allergen.empty() || limit.max_milligrams < 0 || limit.severity <= 0 ||
            !table.emplace(limit.allergen, std::make_pair(limit.max_milligrams, limit.severity)).second) return std::nullopt;
    }
    std::map<std::string, long long> totals;
    for (const auto& exposure : exposures) {
        if (exposure.allergen.empty() || exposure.milligrams < 0) return std::nullopt;
        if (table.count(exposure.allergen)) totals[exposure.allergen] += exposure.milligrams;
    }
    long long score = 0;
    for (const auto& item : totals) {
        const auto limit = table.at(item.first);
        if (item.second > limit.first) score += (item.second - limit.first) * limit.second;
        if (score > INT_MAX) return std::nullopt;
    }
    return static_cast<int>(score);""",
        """assert(contraindication_score({{"nuts",7},{"nuts",5},{"salt",99}},{{"nuts",10,3}})==6);
    assert(contraindication_score({},{}).value()==0);
    assert(!contraindication_score({{"nuts",-1}},{}));
    assert(!contraindication_score({},{{"nuts",1,2},{"nuts",3,4}}));
    assert(!contraindication_score({},{{"",1,2}}));""",
        ["unknown allergens do not contribute", "known exposures aggregate before scoring", "all numeric inputs are validated", "limit allergens are unique", "the returned score must fit int"],
        "validated keyed aggregation followed by checked excess scoring", ["dose", "validation", "checked-arithmetic"],
    )
    add(
        "Allergies", "weighted-symptom-peak", "Weighted symptom peak",
        "Find the maximum concurrent symptom weight inside a half-open observation window. Episodes are half-open, may overlap, and contribute only while intersecting the window. Reject reversed intervals, nonpositive weights, invalid windows, or overflow.",
        "struct SymptomEpisode { int begin; int end; int weight; };",
        "std::optional<int> weighted_symptom_peak(const std::vector<SymptomEpisode>& episodes, int window_begin, int window_end)",
        """if (window_begin > window_end) return std::nullopt;
    std::map<int,long long> events;
    for (const auto& episode : episodes) {
        if (episode.begin > episode.end || episode.weight <= 0) return std::nullopt;
        const int first = std::max(episode.begin, window_begin);
        const int last = std::min(episode.end, window_end);
        if (first < last) { events[first] += episode.weight; events[last] -= episode.weight; }
    }
    long long active = 0, peak = 0;
    for (const auto& event : events) { active += event.second; peak = std::max(peak, active); if (peak > INT_MAX) return std::nullopt; }
    return static_cast<int>(peak);""",
        """assert(weighted_symptom_peak({{0,5,2},{3,7,4}},1,6)==6);
    assert(weighted_symptom_peak({{0,1,9}},1,2)==0);
    assert(weighted_symptom_peak({},4,4)==0);
    assert(!weighted_symptom_peak({{3,2,1}},0,5));
    assert(!weighted_symptom_peak({},5,4));""",
        ["windows and episodes are half-open", "zero-length episodes are valid but inactive", "touching endpoints do not overlap", "weights must be positive", "peak overflow rejects"],
        "clipped sweep-line accumulation with end-before-next-start semantics", ["intervals", "sweep-line", "peak"],
    )
    add(
        "Allergies", "meal-risk-frontier", "Meal risk frontier",
        "For each meal, sum the severities of distinct sensitive ingredients present in that meal and return the stable indices whose score is at least a threshold. Reject empty ingredient names, duplicate sensitivity keys, negative severities, or negative threshold.",
        "struct Sensitivity { std::string ingredient; int severity; };",
        "std::optional<std::vector<std::size_t>> meal_risk_frontier(const std::vector<std::vector<std::string>>& meals, const std::vector<Sensitivity>& sensitivities, int threshold)",
        """if (threshold < 0) return std::nullopt;
    std::map<std::string,int> weight;
    for (const auto& item : sensitivities) if (item.ingredient.empty() || item.severity < 0 || !weight.emplace(item.ingredient,item.severity).second) return std::nullopt;
    std::vector<std::size_t> answer;
    for (std::size_t i=0;i<meals.size();++i) {
        std::set<std::string> seen; long long score=0;
        for (const auto& ingredient : meals[i]) { if (ingredient.empty()) return std::nullopt; if (seen.insert(ingredient).second && weight.count(ingredient)) score += weight.at(ingredient); }
        if (score >= threshold) answer.push_back(i);
    }
    return answer;""",
        """auto r=meal_risk_frontier({{"egg","egg"},{"nut","egg"},{"rice"}},{{"egg",2},{"nut",5}},5);
    assert(r && *r==(std::vector<std::size_t>{1}));
    assert(meal_risk_frontier({}, {}, 0)->empty());
    assert(!meal_risk_frontier({{""}}, {}, 0));
    assert(!meal_risk_frontier({}, {{"x",1},{"x",2}}, 0));""",
        ["meal order determines returned index order", "duplicate ingredients count once per meal", "unknown ingredients contribute zero", "sensitivity keys are unique", "threshold is nonnegative"],
        "per-meal set projection over a validated severity dictionary", ["frontier", "set-projection", "stable-order"],
    )

    add(
        "Bank Account", "escrow-milestone-release", "Escrow milestone release",
        "Replay uniquely named escrow milestones against an initial balance. Completed milestones release their amount in declaration order; disputed milestones remain held. Reject duplicate or empty names, negative amounts, unknown completion names, or overflow.",
        "struct Milestone { std::string name; long long amount; bool disputed; };",
        "std::optional<std::pair<long long,long long>> release_escrow(long long initial_balance, const std::vector<Milestone>& milestones, const std::vector<std::string>& completed)",
        """if (initial_balance < 0) return std::nullopt;
    std::map<std::string,Milestone> by_name;
    long long held=0;
    for (const auto& m : milestones) { if (m.name.empty()||m.amount<0||!by_name.emplace(m.name,m).second||held>LLONG_MAX-m.amount) return std::nullopt; held+=m.amount; }
    std::set<std::string> done;
    long long released=initial_balance;
    for (const auto& name : completed) { auto it=by_name.find(name); if(it==by_name.end()||!done.insert(name).second)return std::nullopt; if(!it->second.disputed){ if(released>LLONG_MAX-it->second.amount)return std::nullopt; released+=it->second.amount; held-=it->second.amount; } }
    return std::make_pair(released,held);""",
        """auto r=release_escrow(10,{{"build",7,false},{"paint",3,true}}, {"build","paint"});assert(r&&r->first==17&&r->second==3);
    assert(release_escrow(0,{},{}).value()==std::make_pair(0LL,0LL));
    assert(!release_escrow(0,{{"x",1,false}}, {"y"}));
    assert(!release_escrow(0,{{"x",1,false}}, {"x","x"}));
    assert(!release_escrow(-1,{},{}));""",
        ["completion names are unique and known", "disputed amounts remain held", "declaration order does not change totals", "all monetary inputs are nonnegative", "both held and released arithmetic is checked"],
        "validated milestone replay into released and held balances", ["escrow", "replay", "money"],
    )
    add(
        "Bank Account", "minimum-daily-balance-audit", "Minimum daily balance audit",
        "Given sorted balance-changing postings, report the earliest time and value of the minimum running balance over an inclusive day. Equal timestamps apply in input order. Reject unsorted/out-of-day postings or arithmetic overflow.",
        "struct TimedPosting { int minute; long long delta; };",
        "std::optional<std::pair<int,long long>> minimum_daily_balance(long long opening, const std::vector<TimedPosting>& postings)",
        """long long balance=opening,best=opening;int best_minute=0;int previous=-1;
    for(const auto& p:postings){if(p.minute<0||p.minute>=1440||p.minute<previous)return std::nullopt;previous=p.minute;if((p.delta>0&&balance>LLONG_MAX-p.delta)||(p.delta<0&&balance<LLONG_MIN-p.delta))return std::nullopt;balance+=p.delta;if(balance<best){best=balance;best_minute=p.minute;}}
    return std::make_pair(best_minute,best);""",
        """assert(minimum_daily_balance(10,{{5,-3},{5,-9},{8,20}}).value()==std::make_pair(5,-2LL));
    assert(minimum_daily_balance(-4,{}).value()==std::make_pair(0,-4LL));
    assert(!minimum_daily_balance(0,{{2,1},{1,1}}));
    assert(!minimum_daily_balance(0,{{1440,1}}));""",
        ["opening balance is observed at minute zero", "equal timestamps preserve input order", "the earliest strict minimum wins", "minutes lie within one day", "running addition is checked"],
        "stable chronological fold retaining the first strict minimum", ["ledger", "minimum", "chronology"],
    )
    add(
        "Bank Account", "tiered-fee-reconciliation", "Tiered fee reconciliation",
        "Reconcile an ordered posting ledger with tiered debit fees. Each negative posting pays the first fee whose absolute debit does not exceed that tier's inclusive cap; a zero cap is the final unbounded tier. Reject malformed tiers and checked-balance overflow.",
        "struct DebitTier { long long inclusive_cap; long long fee; };",
        "std::optional<long long> reconcile_tiered_fees(long long opening, const std::vector<long long>& postings, const std::vector<DebitTier>& tiers)",
        """if(tiers.empty())return std::nullopt;long long previous=-1;bool unbounded=false;for(std::size_t i=0;i<tiers.size();++i){const auto&t=tiers[i];if(t.fee<0||t.inclusive_cap<0||unbounded)return std::nullopt;if(t.inclusive_cap==0){unbounded=true;if(i+1!=tiers.size())return std::nullopt;}else if(t.inclusive_cap<=previous)return std::nullopt;else previous=t.inclusive_cap;}if(!unbounded)return std::nullopt;
    long long balance=opening;for(long long amount:postings){if((amount>0&&balance>LLONG_MAX-amount)||(amount<0&&balance<LLONG_MIN-amount))return std::nullopt;balance+=amount;if(amount<0){if(amount==LLONG_MIN)return std::nullopt;const long long debit=-amount;long long fee=0;for(const auto&t:tiers)if(t.inclusive_cap==0||debit<=t.inclusive_cap){fee=t.fee;break;}if(balance<LLONG_MIN+fee)return std::nullopt;balance-=fee;}}return balance;""",
        """assert(reconcile_tiered_fees(100,{-5,-20,10},{{10,1},{0,3}})==81);
    assert(reconcile_tiered_fees(7,{},{{0,0}})==7);
    assert(!reconcile_tiered_fees(0,{},{}));
    assert(!reconcile_tiered_fees(0,{},{{10,1}}));
    assert(!reconcile_tiered_fees(0,{},{{10,1},{5,2},{0,3}}));""",
        ["tiers are strictly increasing before the final unbounded tier", "only debits incur fees", "debit magnitude handles LLONG_MIN", "posting and fee subtraction are checked", "ledger order is observable"],
        "validated tier lookup embedded in a checked ledger fold", ["fees", "tiers", "reconciliation"],
    )

    add(
        "Binary Search Tree", "avl-rotation-trace-check", "AVL rotation trace check",
        "Validate a declared sequence of single left/right rotations over an indexed binary tree. Every step must name live linked nodes with the required child, preserve the root connection, and finish with a structurally valid tree whose inorder keys equal the original inorder keys.",
        "struct IndexedNode { int key; int left; int right; };\nenum class Turn { left, right };\nstruct Rotation { int pivot; Turn turn; };",
        "bool validate_rotation_trace(std::vector<IndexedNode> nodes, int root, const std::vector<Rotation>& rotations)",
        """auto valid_index=[&](int i){return i>=-1&&i<static_cast<int>(nodes.size());};if(!valid_index(root))return false;for(const auto&n:nodes)if(!valid_index(n.left)||!valid_index(n.right))return false;
    auto traversal=[&](const std::vector<IndexedNode>& tree,int start){std::vector<int> out;std::vector<int> stack;std::set<int> seen;int cur=start;while(cur!=-1||!stack.empty()){while(cur!=-1){if(!seen.insert(cur).second)return std::vector<int>{};stack.push_back(cur);cur=tree[cur].left;}cur=stack.back();stack.pop_back();out.push_back(tree[cur].key);cur=tree[cur].right;}return out;};const auto before=traversal(nodes,root);if(root!=-1&&before.empty())return false;
    for(const auto&step:rotations){if(step.pivot<0||step.pivot>=static_cast<int>(nodes.size()))return false;int parent=-1;for(int i=0;i<static_cast<int>(nodes.size());++i)if(nodes[i].left==step.pivot||nodes[i].right==step.pivot){if(parent!=-1)return false;parent=i;}int child=step.turn==Turn::left?nodes[step.pivot].right:nodes[step.pivot].left;if(child<0)return false;if(step.turn==Turn::left){nodes[step.pivot].right=nodes[child].left;nodes[child].left=step.pivot;}else{nodes[step.pivot].left=nodes[child].right;nodes[child].right=step.pivot;}if(parent==-1)root=child;else if(nodes[parent].left==step.pivot)nodes[parent].left=child;else nodes[parent].right=child;}
    return traversal(nodes,root)==before;""",
        """assert(validate_rotation_trace({{1,-1,1},{2,-1,-1}},0,{{0,Turn::left}}));
    assert(validate_rotation_trace({},-1,{}));
    assert(!validate_rotation_trace({{1,-1,-1}},0,{{0,Turn::left}}));
    assert(!validate_rotation_trace({{1,0,-1}},0,{}));
    assert(!validate_rotation_trace({{1,-1,-1}},2,{}));""",
        ["all child indices and the root are validated", "cycles and shared parents reject", "each pivot must be linked and have the required child", "root rotations reconnect correctly", "inorder key sequence is invariant"],
        "indexed pointer rewrites guarded by before/after inorder invariance", ["tree", "rotation", "trace-validation"],
    )
    add(
        "Binary Search Tree", "persistent-version-delta", "Persistent version delta",
        "Compare two immutable BST versions represented by sorted unique key/value pairs. Return keys inserted, erased, or value-changed in ascending order. Reject either version if keys are not strictly increasing.",
        "struct KeyValue { int key; int value; };\nstruct VersionDelta { std::vector<int> inserted; std::vector<int> erased; std::vector<int> changed; };",
        "std::optional<VersionDelta> persistent_version_delta(const std::vector<KeyValue>& before, const std::vector<KeyValue>& after)",
        """auto ordered=[](const std::vector<KeyValue>&v){for(std::size_t i=1;i<v.size();++i)if(v[i-1].key>=v[i].key)return false;return true;};if(!ordered(before)||!ordered(after))return std::nullopt;VersionDelta d;std::size_t i=0,j=0;while(i<before.size()||j<after.size()){if(j==after.size()||(i<before.size()&&before[i].key<after[j].key))d.erased.push_back(before[i++].key);else if(i==before.size()||after[j].key<before[i].key)d.inserted.push_back(after[j++].key);else{if(before[i].value!=after[j].value)d.changed.push_back(before[i].key);++i;++j;}}return d;""",
        """auto d=persistent_version_delta({{1,4},{3,9}},{{2,5},{3,8}});assert(d&&d->inserted==(std::vector<int>{2})&&d->erased==(std::vector<int>{1})&&d->changed==(std::vector<int>{3}));
    assert(persistent_version_delta({},{})->changed.empty());
    assert(!persistent_version_delta({{1,0},{1,2}},{}));
    assert(!persistent_version_delta({},{{2,0},{1,0}}));""",
        ["both inputs are strictly key-sorted", "inserted, erased, and changed sets are disjoint", "unchanged values are omitted", "outputs are ascending", "empty versions are valid"],
        "two-way ordered merge classifying key membership and value changes", ["persistent-tree", "diff", "ordered-merge"],
    )
    add(
        "Binary Search Tree", "preorder-parent-reconstruction", "Preorder parent reconstruction",
        "Reconstruct parent indices from the preorder of a strict BST without building nodes. The first key has parent -1; each later key is attached to the last valid ancestor according to strict lower/upper bounds. Reject duplicates or impossible bound transitions.",
        "",
        "std::optional<std::vector<int>> preorder_parent_indices(const std::vector<int>& preorder)",
        """if(preorder.empty())return std::vector<int>{};std::vector<int> stack{0};std::vector<int> parent(preorder.size(),-1);long long lower=LLONG_MIN;for(std::size_t i=1;i<preorder.size();++i){const long long key=preorder[i];if(key<=lower)return std::nullopt;if(key<preorder[stack.back()])parent[i]=stack.back();else{int last=-1;while(!stack.empty()&&key>preorder[stack.back()]){last=stack.back();lower=preorder[stack.back()];stack.pop_back();}if(last<0||( !stack.empty()&&key==preorder[stack.back()] ))return std::nullopt;parent[i]=last;}stack.push_back(static_cast<int>(i));}return parent;""",
        """auto p=preorder_parent_indices({8,3,1,6,10,14});assert(p&&*p==(std::vector<int>{-1,0,1,1,0,4}));
    assert(preorder_parent_indices({})->empty());
    assert(preorder_parent_indices({5}).value()==(std::vector<int>{-1}));
    assert(!preorder_parent_indices({5,5}));
    assert(!preorder_parent_indices({8,3,10,2}));""",
        ["the BST ordering is strict", "the empty preorder returns an empty parent vector", "root parent is -1", "every later parent precedes its child", "a value outside all open ancestor bounds rejects"],
        "ancestor stack with open numeric bounds", ["preorder", "reconstruction", "bounds"],
    )

    add(
        "Circular Buffer", "sequence-gap-ranges", "Sequence gap ranges",
        "Decode missing sequence ranges from a bounded modular packet window. Packet numbers advance modulo modulus from an expected start, duplicates are ignored, and numbers outside the forward window reject. Return missing offsets as maximal inclusive ranges.",
        "",
        "std::optional<std::vector<std::pair<int,int>>> missing_sequence_ranges(int modulus, int expected, int window, const std::vector<int>& received)",
        """if(modulus<=0||expected<0||expected>=modulus||window<0||window>=modulus)return std::nullopt;std::set<int> offsets;for(int value:received){if(value<0||value>=modulus)return std::nullopt;int offset=(value-expected+modulus)%modulus;if(offset>window)return std::nullopt;offsets.insert(offset);}std::vector<std::pair<int,int>> out;for(int i=0;i<=window;){if(offsets.count(i)){++i;continue;}int first=i;while(i+1<=window&&!offsets.count(i+1))++i;out.push_back({first,i});++i;}return out;""",
        """auto r=missing_sequence_ranges(8,6,4,{6,0,2,0});assert(r&&*r==(std::vector<std::pair<int,int>>{{1,1},{3,3}}));
    assert(missing_sequence_ranges(5,1,0,{1})->empty());
    assert(!missing_sequence_ranges(5,1,5,{}));
    assert(!missing_sequence_ranges(5,1,2,{4}));""",
        ["window is smaller than modulus", "duplicates are ignored", "wraparound offsets are forward modular distances", "out-of-window packets reject", "missing offsets coalesce maximally"],
        "modular offset validation followed by maximal complement runs", ["sequence", "gaps", "modular-window"],
    )
    add(
        "Circular Buffer", "snapshot-delta-runs", "Snapshot delta runs",
        "Compare two equally sized logical ring snapshots with independent head indices. Return maximal logical index runs whose values differ. Reject invalid heads or unequal physical sizes; empty rings require head zero.",
        "struct ChangedRun { std::size_t first; std::size_t count; };",
        "std::optional<std::vector<ChangedRun>> ring_snapshot_delta(const std::vector<int>& before, std::size_t before_head, const std::vector<int>& after, std::size_t after_head)",
        """if(before.size()!=after.size())return std::nullopt;const std::size_t n=before.size();if((n==0&&(before_head!=0||after_head!=0))||(n>0&&(before_head>=n||after_head>=n)))return std::nullopt;std::vector<ChangedRun> out;std::size_t i=0;while(i<n){if(before[(before_head+i)%n]==after[(after_head+i)%n]){++i;continue;}const std::size_t first=i;while(i<n&&before[(before_head+i)%n]!=after[(after_head+i)%n])++i;out.push_back({first,i-first});}return out;""",
        """auto r=ring_snapshot_delta({3,1,2},1,{1,9,3},0);assert(r&&r->size()==1&&r->at(0).first==1&&r->at(0).count==1);
    assert(ring_snapshot_delta({},0,{},0)->empty());
    assert(!ring_snapshot_delta({},1,{},0));
    assert(!ring_snapshot_delta({1},0,{1,2},0));
    assert(!ring_snapshot_delta({1},1,{1},0));""",
        ["logical order begins at each independent head", "physical sizes must match", "empty heads must be zero", "changed runs never wrap logically", "adjacent differences coalesce"],
        "head-relative comparison with maximal logical difference runs", ["snapshot", "delta", "ring"],
    )
    add(
        "Circular Buffer", "timing-bucket-compaction", "Timing bucket compaction",
        "Compact a circular timing wheel into stable due-event groups. Every event has a nonnegative delay strictly below wheel_size times rounds; group by the slot reached from the current slot and then by complete rounds, preserving event input order inside equal groups.",
        "struct DelayedEvent { std::string id; int delay; };\nstruct DueGroup { int rounds; int slot; std::vector<std::string> ids; };",
        "std::optional<std::vector<DueGroup>> compact_timing_buckets(int wheel_size, int current_slot, int max_rounds, const std::vector<DelayedEvent>& events)",
        """if(wheel_size<=0||current_slot<0||current_slot>=wheel_size||max_rounds<=0)return std::nullopt;std::map<std::pair<int,int>,std::vector<std::string>> groups;std::set<std::string> ids;for(const auto&e:events){if(e.id.empty()||!ids.insert(e.id).second||e.delay<0||e.delay>=wheel_size*max_rounds)return std::nullopt;const int total=current_slot+e.delay;groups[{total/wheel_size,(total%wheel_size)}].push_back(e.id);}std::vector<DueGroup> out;for(const auto&g:groups)out.push_back({g.first.first,g.first.second,g.second});return out;""",
        """auto r=compact_timing_buckets(4,3,3,{{"a",1},{"b",5},{"c",1}});assert(r&&r->size()==2&&r->at(0).ids==(std::vector<std::string>{"a","c"}));
    assert(compact_timing_buckets(3,0,1,{})->empty());
    assert(!compact_timing_buckets(0,0,1,{}));
    assert(!compact_timing_buckets(4,0,1,{{"x",4}}));
    assert(!compact_timing_buckets(4,0,1,{{"x",0},{"x",1}}));""",
        ["event IDs are nonempty and unique", "delay bounds are strict", "slot arithmetic includes the current slot", "groups sort by complete rounds then slot", "equal-group input order is stable"],
        "validated modular scheduling into ordered composite-key groups", ["timing-wheel", "grouping", "stable-order"],
    )

    add(
        "Clock", "weekly-cron-next", "Weekly cron next occurrence",
        "Find the first weekly minute at or after a start that matches a set of weekdays and minute-of-day values, wrapping once if needed. Inputs are canonical sorted unique sets and the start lies in one week. Empty schedules have no result.",
        "",
        "std::optional<int> next_weekly_occurrence(const std::vector<int>& weekdays, const std::vector<int>& minutes_of_day, int start_week_minute)",
        """if(start_week_minute<0||start_week_minute>=10080)return std::nullopt;auto canonical=[](const std::vector<int>&v,int hi){for(std::size_t i=0;i<v.size();++i)if(v[i]<0||v[i]>=hi||(i&&v[i-1]>=v[i]))return false;return true;};if(!canonical(weekdays,7)||!canonical(minutes_of_day,1440))return std::nullopt;if(weekdays.empty()||minutes_of_day.empty())return std::nullopt;for(int delta=0;delta<10080;++delta){int t=(start_week_minute+delta)%10080;int d=t/1440,m=t%1440;if(std::binary_search(weekdays.begin(),weekdays.end(),d)&&std::binary_search(minutes_of_day.begin(),minutes_of_day.end(),m))return t;}return std::nullopt;""",
        """assert(next_weekly_occurrence({1,3},{60,120},1*1440+61)==1*1440+120);
    assert(next_weekly_occurrence({0},{0},10079)==0);
    assert(!next_weekly_occurrence({}, {1}, 0));
    assert(!next_weekly_occurrence({2,1},{1},0));
    assert(!next_weekly_occurrence({0},{1440},0));""",
        ["weekdays and minutes are sorted unique", "start is included in the search", "one wrap is permitted", "empty schedule has no occurrence", "results are normalized weekly minutes"],
        "bounded modular scan over canonical schedule sets", ["cron", "weekly", "search"],
    )
    add(
        "Clock", "timetable-free-gaps", "Timetable free gaps",
        "Normalize possibly overlapping half-open busy intervals within a day and return free gaps of at least a requested duration. Reject intervals outside the day, reversed intervals, or negative minimum duration.",
        "struct MinuteInterval { int begin; int end; };",
        "std::optional<std::vector<MinuteInterval>> timetable_free_gaps(int day_minutes, const std::vector<MinuteInterval>& busy, int minimum_duration)",
        """if(day_minutes<0||minimum_duration<0)return std::nullopt;std::vector<MinuteInterval> sorted=busy;for(const auto&i:sorted)if(i.begin<0||i.end<i.begin||i.end>day_minutes)return std::nullopt;std::sort(sorted.begin(),sorted.end(),[](const auto&a,const auto&b){return std::tie(a.begin,a.end)<std::tie(b.begin,b.end);});std::vector<MinuteInterval> out;int cursor=0;for(const auto&i:sorted){if(i.begin-cursor>=minimum_duration)out.push_back({cursor,i.begin});cursor=std::max(cursor,i.end);}if(day_minutes-cursor>=minimum_duration)out.push_back({cursor,day_minutes});return out;""",
        """auto r=timetable_free_gaps(10,{{2,4},{3,7}},2);assert(r&&r->size()==2&&r->at(0).begin==0&&r->at(1).begin==7);
    assert(timetable_free_gaps(0,{},0)->size()==1);
    assert(!timetable_free_gaps(5,{{4,3}},0));
    assert(!timetable_free_gaps(5,{{0,6}},0));
    assert(!timetable_free_gaps(5,{},-1));""",
        ["busy intervals are half-open", "overlapping and touching busy intervals merge", "zero-length intervals do not consume time", "minimum zero includes zero-size boundary gaps", "input order is irrelevant"],
        "sort-and-merge busy coverage while emitting bounded complements", ["timetable", "interval-union", "free-time"],
    )
    add(
        "Clock", "leap-offset-table-conversion", "Leap offset table conversion",
        "Convert a monotonic atomic second to civil seconds using a sorted table of offset changes. Each change applies from its atomic second onward. Reject unsorted/duplicate change points or checked subtraction overflow.",
        "struct OffsetChange { long long atomic_second; int total_offset; };",
        "std::optional<long long> atomic_to_civil(long long atomic_second, const std::vector<OffsetChange>& changes)",
        """for(std::size_t i=1;i<changes.size();++i)if(changes[i-1].atomic_second>=changes[i].atomic_second)return std::nullopt;int offset=0;for(const auto&c:changes){if(c.atomic_second>atomic_second)break;offset=c.total_offset;}if(offset>0&&atomic_second<LLONG_MIN+offset)return std::nullopt;if(offset<0&&atomic_second>LLONG_MAX+offset)return std::nullopt;return atomic_second-offset;""",
        """assert(atomic_to_civil(99,{{100,10}})==99);
    assert(atomic_to_civil(100,{{100,10}})==90);
    assert(atomic_to_civil(250,{{100,10},{200,11}})==239);
    assert(!atomic_to_civil(0,{{1,1},{1,2}}));
    assert(!atomic_to_civil(LLONG_MIN,{{LLONG_MIN,1}}));""",
        ["change points are strictly increasing", "the latest applicable total offset wins", "no change means offset zero", "negative offsets are allowed", "subtraction is overflow-checked"],
        "upper-bound selection in a validated piecewise offset table", ["time-scale", "piecewise-table", "overflow"],
    )

    add(
        "Complex Numbers", "roots-of-unity-spectrum", "Roots of unity spectrum",
        "Compute the discrete Fourier spectrum of real samples directly using the negative-angle convention. Reject empty input above the configured bound or non-finite samples; normalize tiny real and imaginary components to exact zero.",
        "",
        "std::optional<std::vector<std::complex<double>>> roots_of_unity_spectrum(const std::vector<double>& samples, std::size_t maximum_size)",
        """if(samples.size()>maximum_size)return std::nullopt;for(double x:samples)if(!std::isfinite(x))return std::nullopt;std::vector<std::complex<double>> out(samples.size());const double pi=std::acos(-1.0);for(std::size_t k=0;k<samples.size();++k)for(std::size_t n=0;n<samples.size();++n){double a=-2.0*pi*static_cast<double>(k*n)/static_cast<double>(samples.size());out[k]+=samples[n]*std::complex<double>(std::cos(a),std::sin(a));}for(auto&z:out){if(std::abs(z.real())<1e-12)z.real(0);if(std::abs(z.imag())<1e-12)z.imag(0);}return out;""",
        """auto r=roots_of_unity_spectrum({1,0,-1,0},4);assert(r&&r->size()==4&&std::abs(r->at(1).real()-2.0)<1e-9&&std::abs(r->at(1).imag())<1e-9);
    assert(roots_of_unity_spectrum({},0)->empty());
    assert(!roots_of_unity_spectrum({1,2},1));
    assert(!roots_of_unity_spectrum({std::numeric_limits<double>::infinity()},1));""",
        ["sample count is explicitly bounded", "empty input returns empty output", "non-finite samples reject", "negative-angle DFT convention is fixed", "numerical dust below tolerance becomes signed-free zero"],
        "bounded direct DFT using roots of unity", ["complex", "dft", "numerical"],
    )
    add(
        "Complex Numbers", "principal-phase-unwrapper", "Principal phase unwrapper",
        "Unwrap a sequence of principal phases from [-pi, pi] by adding integer turns so each adjacent delta lies in (-pi, pi], choosing the positive endpoint on an exact tie. Reject non-finite or out-of-domain values.",
        "",
        "std::optional<std::vector<double>> unwrap_principal_phases(const std::vector<double>& phases)",
        """const double pi=std::acos(-1.0);std::vector<double> out;if(phases.empty())return out;for(double x:phases)if(!std::isfinite(x)||x<-pi||x>pi)return std::nullopt;out.push_back(phases[0]);for(std::size_t i=1;i<phases.size();++i){double delta=phases[i]-phases[i-1];while(delta<=-pi)delta+=2*pi;while(delta>pi)delta-=2*pi;out.push_back(out.back()+delta);}return out;""",
        """const double p=std::acos(-1.0);auto r=unwrap_principal_phases({3.0,-3.0,-2.5});assert(r&&r->at(1)>3.0&&std::abs(r->at(2)-3.783185307179586)<1e-9);
    assert(unwrap_principal_phases({})->empty());
    assert(unwrap_principal_phases({p/2,-p/2})->at(1)>p);
    assert(!unwrap_principal_phases({p+0.1}));
    assert(!unwrap_principal_phases({std::numeric_limits<double>::quiet_NaN()}));""",
        ["input principal domain is closed [-pi, pi]", "output begins exactly at the first phase", "adjacent unwrapped deltas use (-pi, pi]", "negative-pi ties map to positive pi", "all inputs are finite"],
        "incremental modular phase-delta normalization", ["phase", "unwrap", "calibration"],
    )
    add(
        "Complex Numbers", "bounded-newton-orbit", "Bounded Newton orbit",
        "Iterate Newton's method for z squared minus c from an initial complex value. Return the first iteration count whose residual is within tolerance, zero if already converged, or no value after the limit. Reject non-finite inputs, invalid tolerance, or a zero derivative.",
        "",
        "std::optional<std::optional<std::size_t>> bounded_newton_orbit(std::complex<double> initial, std::complex<double> c, double tolerance, std::size_t limit)",
        """auto finite=[](std::complex<double>z){return std::isfinite(z.real())&&std::isfinite(z.imag());};if(!finite(initial)||!finite(c)||!std::isfinite(tolerance)||tolerance<0)return std::nullopt;std::complex<double> z=initial;for(std::size_t i=0;i<=limit;++i){if(std::abs(z*z-c)<=tolerance)return std::optional<std::size_t>{i};if(i==limit)break;if(z==std::complex<double>{})return std::nullopt;z=(z+c/z)/2.0;if(!finite(z))return std::nullopt;}return std::optional<std::size_t>{};""",
        """auto r=bounded_newton_orbit({2,0},{4,0},1e-12,4);assert(r&&*r&&**r==0);
    auto q=bounded_newton_orbit({1,0},{4,0},1e-6,20);assert(q&&*q);
    assert(!bounded_newton_orbit({0,0},{4,0},0.0,2));
    auto none=bounded_newton_orbit({1,0},{2,0},0.0,0);assert(none&&!*none);
    assert(!bounded_newton_orbit({1,0},{2,0},-1,2));""",
        ["outer optional reports invalid iteration", "inner optional reports convergence", "initial convergence returns zero", "zero derivative rejects", "iteration limit is inclusive of the starting residual"],
        "guarded Newton iteration with nested validity/convergence result", ["newton", "complex", "bounded-iteration"],
    )

    add(
        "Crypto Square", "rail-fence-codec", "Rail fence codec",
        "Encode or decode a rail-fence transposition over bytes using a fixed rail count. One rail is identity; empty text is valid. Reject zero rails or rail counts greater than text length for nonempty text.",
        "enum class RailMode { encode, decode };",
        "std::optional<std::string> rail_fence_transform(std::string_view text, std::size_t rails, RailMode mode)",
        """if(rails==0||(!text.empty()&&rails>text.size()))return std::nullopt;if(text.empty()||rails==1)return std::string(text);std::vector<std::size_t> path;for(std::size_t i=0,row=0; i<text.size(); ++i){path.push_back(row);const std::size_t period=2*(rails-1),phase=(i+1)%period;row=phase<rails?phase:period-phase;}std::string out(text.size(),' ');if(mode==RailMode::encode){std::size_t w=0;for(std::size_t r=0;r<rails;++r)for(std::size_t i=0;i<text.size();++i)if(path[i]==r)out[w++]=text[i];}else{std::vector<std::size_t> positions;for(std::size_t r=0;r<rails;++r)for(std::size_t i=0;i<path.size();++i)if(path[i]==r)positions.push_back(i);for(std::size_t i=0;i<text.size();++i)out[positions[i]]=text[i];}return out;""",
        """auto e=rail_fence_transform("WEAREDISCOVERED",3,RailMode::encode);assert(e&&rail_fence_transform(*e,3,RailMode::decode)==std::optional<std::string>{"WEAREDISCOVERED"});
    assert(rail_fence_transform("abc",1,RailMode::encode)==std::optional<std::string>{"abc"});
    assert(rail_fence_transform("",2,RailMode::decode)==std::optional<std::string>{""});
    assert(!rail_fence_transform("a",2,RailMode::encode));
    assert(!rail_fence_transform("abc",0,RailMode::encode));""",
        ["all byte values are preserved", "encode and decode are exact inverses", "one rail is identity", "empty text permits any positive rail count", "nonempty rail count cannot exceed length"],
        "zigzag position schedule with stable rail concatenation/inversion", ["transposition", "codec", "rail-fence"],
    )
    add(
        "Crypto Square", "checkerboard-coordinate-pack", "Checkerboard coordinate pack",
        "Encode symbols through a rectangular keyed checkerboard into row/column digit pairs. The alphabet must be nonempty and unique, dimensions must exactly cover it, and plaintext symbols must be known. Digits are zero-based decimal, so each dimension is at most ten.",
        "",
        "std::optional<std::string> checkerboard_pack(std::string_view alphabet, std::size_t columns, std::string_view plaintext)",
        """if(alphabet.empty()||columns==0||columns>10)return std::nullopt;std::set<char> unique(alphabet.begin(),alphabet.end());if(unique.size()!=alphabet.size())return std::nullopt;const std::size_t rows=(alphabet.size()+columns-1)/columns;if(rows>10||rows*columns!=alphabet.size())return std::nullopt;std::string out;for(char c:plaintext){auto pos=alphabet.find(c);if(pos==std::string_view::npos)return std::nullopt;out.push_back(static_cast<char>('0'+pos/columns));out.push_back(static_cast<char>('0'+pos%columns));}return out;""",
        """assert(checkerboard_pack("abcdef",3,"face")==std::optional<std::string>{"12000211"});
    assert(checkerboard_pack("ab",2,"")==std::optional<std::string>{""});
    assert(!checkerboard_pack("aba",1,"a"));
    assert(!checkerboard_pack("abc",2,"a"));
    assert(!checkerboard_pack("ab",2,"x"));""",
        ["alphabet symbols are unique", "rectangle has no padding cells", "row and column digits are zero-based", "dimensions fit one decimal digit", "unknown plaintext symbols reject"],
        "direct keyed-symbol lookup into rectangular decimal coordinates", ["checkerboard", "coordinates", "validation"],
    )
    add(
        "Crypto Square", "transposed-block-checksum", "Transposed block checksum",
        "Partition bytes into exact-width blocks, apply a declared column permutation, and return one XOR checksum byte per output column across all blocks. Reject partial blocks or a non-permutation of columns.",
        "",
        "std::optional<std::vector<unsigned char>> transposed_block_checksum(const std::vector<unsigned char>& bytes, std::size_t width, const std::vector<std::size_t>& output_to_input)",
        """if(width==0||output_to_input.size()!=width||bytes.size()%width!=0)return std::nullopt;std::vector<bool> seen(width);for(auto x:output_to_input)if(x>=width||seen[x])return std::nullopt;else seen[x]=true;std::vector<unsigned char> out(width,0);for(std::size_t base=0;base<bytes.size();base+=width)for(std::size_t column=0;column<width;++column)out[column]^=bytes[base+output_to_input[column]];return out;""",
        """auto r=transposed_block_checksum({1,2,3,4,5,6},3,{2,0,1});assert(r&&*r==(std::vector<unsigned char>{static_cast<unsigned char>(3^6),static_cast<unsigned char>(1^4),static_cast<unsigned char>(2^5)}));
    assert(transposed_block_checksum({},2,{1,0}).value()==(std::vector<unsigned char>{0,0}));
    assert(!transposed_block_checksum({1},2,{0,1}));
    assert(!transposed_block_checksum({},2,{0,0}));
    assert(!transposed_block_checksum({},0,{}));""",
        ["width is positive", "input contains whole blocks", "column map is a full permutation", "empty block set returns zero checksums", "XOR operates on unsigned bytes"],
        "permuted column reduction over exact-width byte blocks", ["block", "permutation", "checksum"],
    )

    add(
        "Diamond", "l1-binary-dilation", "L1 binary dilation",
        "Dilate true cells in a rectangular Boolean image by an integer Manhattan radius and return the resulting image. Reject ragged images or negative radius; an empty image and zero-width rows are valid.",
        "",
        "std::optional<std::vector<std::vector<bool>>> l1_dilate(const std::vector<std::vector<bool>>& image, int radius)",
        """if(radius<0)return std::nullopt;const std::size_t rows=image.size(),cols=rows?image[0].size():0;for(const auto&row:image)if(row.size()!=cols)return std::nullopt;auto out=image;for(std::size_t r=0;r<rows;++r)for(std::size_t c=0;c<cols;++c)if(image[r][c])for(std::size_t rr=0;rr<rows;++rr)for(std::size_t cc=0;cc<cols;++cc)if(std::llabs(static_cast<long long>(r)-static_cast<long long>(rr))+std::llabs(static_cast<long long>(c)-static_cast<long long>(cc))<=radius)out[rr][cc]=true;return out;""",
        """auto r=l1_dilate({{false,false,false},{false,true,false},{false,false,false}},1);assert(r&&r->at(0).at(1)&&r->at(1).at(0)&&!r->at(0).at(0));
    assert(l1_dilate({},3)->empty());
    assert(l1_dilate({{}},0)->size()==1);
    assert(!l1_dilate({{true},{false,true}},1));
    assert(!l1_dilate({},-1));""",
        ["shape is rectangular", "distance is Manhattan", "source cells remain true", "zero radius is identity", "empty dimensions are preserved"],
        "bounded all-pairs Manhattan neighborhood marking", ["binary-image", "dilation", "manhattan"],
    )
    add(
        "Diamond", "rhombus-overlap-lattice-count", "Rhombus overlap lattice count",
        "Count integer lattice points contained in both closed Manhattan balls. Centers and nonnegative radii are integral; reject negative radii or if the finite bounding-box count would exceed size_t.",
        "struct L1Ball { long long row; long long column; long long radius; };",
        "std::optional<std::size_t> rhombus_overlap_lattice_count(L1Ball first, L1Ball second)",
        """if(first.radius<0||second.radius<0)return std::nullopt;const long long lo_r=std::max(first.row-first.radius,second.row-second.radius),hi_r=std::min(first.row+first.radius,second.row+second.radius);const long long lo_c=std::max(first.column-first.radius,second.column-second.radius),hi_c=std::min(first.column+first.radius,second.column+second.radius);if(lo_r>hi_r||lo_c>hi_c)return std::size_t{0};std::size_t count=0;for(long long r=lo_r;;++r){for(long long c=lo_c;;++c){if(std::llabs(r-first.row)+std::llabs(c-first.column)<=first.radius&&std::llabs(r-second.row)+std::llabs(c-second.column)<=second.radius){if(count==std::numeric_limits<std::size_t>::max())return std::nullopt;++count;}if(c==hi_c)break;}if(r==hi_r)break;}return count;""",
        """assert(rhombus_overlap_lattice_count({0,0,1},{1,0,1})==2);
    assert(rhombus_overlap_lattice_count({0,0,0},{0,0,0})==1);
    assert(rhombus_overlap_lattice_count({0,0,1},{9,9,1})==0);
    assert(!rhombus_overlap_lattice_count({0,0,-1},{0,0,0}));""",
        ["balls are closed", "radii are nonnegative", "disjoint bounding boxes return zero", "center points count", "count overflow rejects"],
        "finite bounding-box enumeration with dual Manhattan predicates", ["lattice", "intersection", "counting"],
    )
    add(
        "Diamond", "rotated-grid-diagonal-profile", "Rotated grid diagonal profile",
        "For a rectangular integer grid, return sums of cells grouped by row+column diagonal followed by sums grouped by row-column diagonal. Each group order is ascending diagonal key. Reject ragged grids or sum overflow.",
        "",
        "std::optional<std::vector<long long>> rotated_diagonal_profile(const std::vector<std::vector<int>>& grid)",
        """const std::size_t rows=grid.size(),cols=rows?grid[0].size():0;for(const auto&row:grid)if(row.size()!=cols)return std::nullopt;std::map<long long,long long> down,up;for(std::size_t r=0;r<rows;++r)for(std::size_t c=0;c<cols;++c){auto add=[](long long&a,int v){if((v>0&&a>LLONG_MAX-v)||(v<0&&a<LLONG_MIN-v))return false;a+=v;return true;};if(!add(down[static_cast<long long>(r+c)],grid[r][c])||!add(up[static_cast<long long>(r)-static_cast<long long>(c)],grid[r][c]))return std::nullopt;}std::vector<long long> out;for(const auto&x:down)out.push_back(x.second);for(const auto&x:up)out.push_back(x.second);return out;""",
        """auto r=rotated_diagonal_profile({{1,2},{3,4}});assert(r&&*r==(std::vector<long long>{1,5,4,2,5,3}));
    assert(rotated_diagonal_profile({})->empty());
    assert(rotated_diagonal_profile({{}})->empty());
    assert(!rotated_diagonal_profile({{1},{2,3}}));""",
        ["shape is rectangular", "first profile uses ascending row+column", "second uses ascending row-column", "empty dimensions return no groups", "every group addition is checked"],
        "ordered diagonal-key aggregation in two rotated coordinate systems", ["rotated-grid", "diagonals", "profile"],
    )

    add(
        "Grade School", "weighted-credit-audit", "Weighted credit audit",
        "Compute attempted credits, earned credits, and a reduced exact quality-point fraction from uniquely coded courses. Withdrawn courses add neither credits nor points; failing grades attempt credits but earn none. Reject invalid credits, grade points, or duplicate codes.",
        "struct CourseGrade { std::string code; int credits; int grade_points; bool withdrawn; };\nstruct CreditAudit { int attempted; int earned; long long quality_numerator; long long quality_denominator; };",
        "std::optional<CreditAudit> weighted_credit_audit(const std::vector<CourseGrade>& courses)",
        """std::set<std::string> codes;long long attempted=0,earned=0,quality=0;for(const auto&c:courses){if(c.code.empty()||!codes.insert(c.code).second||c.credits<=0||c.grade_points<0||c.grade_points>4)return std::nullopt;if(c.withdrawn)continue;attempted+=c.credits;if(c.grade_points>0)earned+=c.credits;quality+=static_cast<long long>(c.credits)*c.grade_points;if(attempted>INT_MAX||earned>INT_MAX)return std::nullopt;}long long denominator=attempted?attempted:1;long long g=std::gcd(quality,denominator);return CreditAudit{static_cast<int>(attempted),static_cast<int>(earned),quality/g,denominator/g};""",
        """auto r=weighted_credit_audit({{"A",3,4,false},{"B",2,0,false},{"C",1,3,true}});assert(r&&r->attempted==5&&r->earned==3&&r->quality_numerator==12&&r->quality_denominator==5);
    auto e=weighted_credit_audit({});assert(e&&e->quality_numerator==0&&e->quality_denominator==1);
    assert(!weighted_credit_audit({{"A",0,2,false}}));
    assert(!weighted_credit_audit({{"A",1,2,false},{"A",1,3,false}}));""",
        ["course codes are nonempty and unique", "credits are positive", "grade points lie from zero through four", "withdrawals are excluded", "the quality fraction is reduced and zero uses denominator one"],
        "validated exact rational aggregation over course outcomes", ["credits", "rational", "audit"],
    )
    add(
        "Grade School", "piecewise-curve-inversion", "Piecewise curve inversion",
        "Invert a monotone integer grading curve. Breakpoints map raw inclusive lower bounds to reported grades and are strictly increasing in both dimensions. Return the smallest raw score producing at least a requested grade, or no score when unreachable.",
        "struct CurvePoint { int raw_lower; int reported; };",
        "std::optional<std::optional<int>> invert_grade_curve(const std::vector<CurvePoint>& curve, int requested_reported)",
        """for(std::size_t i=1;i<curve.size();++i)if(curve[i-1].raw_lower>=curve[i].raw_lower||curve[i-1].reported>=curve[i].reported)return std::nullopt;if(curve.empty())return std::optional<int>{};for(const auto&p:curve)if(p.reported>=requested_reported)return std::optional<int>{p.raw_lower};return std::optional<int>{};""",
        """auto r=invert_grade_curve({{0,50},{40,70},{80,90}},69);assert(r&&*r&&**r==40);
    auto low=invert_grade_curve({{10,20}},-5);assert(low&&**low==10);
    auto none=invert_grade_curve({{0,50}},60);assert(none&&!*none);
    assert(!invert_grade_curve({{0,50},{0,60}},55));
    assert(invert_grade_curve({},10)&&!*invert_grade_curve({},10));""",
        ["raw and reported breakpoints are both strictly increasing", "breakpoint lower bounds are inclusive", "the smallest satisfying raw score wins", "unreachable grades use empty inner optional", "malformed curves use empty outer optional"],
        "lower-bound search over a validated monotone step curve", ["curve", "inverse", "nested-result"],
    )
    add(
        "Grade School", "prerequisite-closure-audit", "Prerequisite closure audit",
        "Audit a proposed course plan against completed courses and a prerequisite graph. Course codes and edges are unique; every prerequisite must be completed or appear earlier in the plan. Reject unknown codes, duplicate plan entries, self edges, or cycles in the catalog.",
        "struct Prerequisite { std::string course; std::string required; };",
        "std::optional<bool> prerequisite_closure_audit(const std::vector<std::string>& catalog, const std::vector<Prerequisite>& edges, const std::vector<std::string>& completed, const std::vector<std::string>& plan)",
        """std::set<std::string> known(catalog.begin(),catalog.end());if(known.size()!=catalog.size()||known.count(""))return std::nullopt;std::map<std::string,std::set<std::string>> req;for(const auto&e:edges)if(e.course==e.required||!known.count(e.course)||!known.count(e.required)||!req[e.course].insert(e.required).second)return std::nullopt;std::map<std::string,int> color;std::function<bool(const std::string&)> dfs=[&](const std::string&x){if(color[x]==1)return false;if(color[x]==2)return true;color[x]=1;for(const auto&y:req[x])if(!dfs(y))return false;color[x]=2;return true;};for(const auto&x:catalog)if(!dfs(x))return std::nullopt;std::set<std::string> available;for(const auto&x:completed)if(!known.count(x)||!available.insert(x).second)return std::nullopt;for(const auto&x:plan){if(!known.count(x)||available.count(x))return std::nullopt;for(const auto&y:req[x])if(!available.count(y))return false;available.insert(x);}return true;""",
        """assert(prerequisite_closure_audit({"A","B","C"},{{"C","B"},{"B","A"}},{"A"},{"B","C"})==true);
    assert(prerequisite_closure_audit({"A","B"},{{"B","A"}},{},{"B"})==false);
    assert(!prerequisite_closure_audit({"A","B"},{{"A","B"},{"B","A"}},{},{}));
    assert(!prerequisite_closure_audit({"A"},{},{"X"},{}));""",
        ["catalog codes are unique and nonempty", "graph edges are unique and known", "catalog cycles reject structurally", "completed and plan courses cannot repeat", "plan order must close every prerequisite"],
        "catalog DAG validation followed by ordered availability closure", ["prerequisite", "dag", "audit"],
    )

    add(
        "Kindergarten Garden", "irrigation-deficit-allocation", "Irrigation deficit allocation",
        "Allocate a fixed water budget across plots in input order up to each plot's nonnegative deficit after rainfall and retention. Retention is a percentage from zero through one hundred. Return applied units and unmet total; reject overflow or malformed plots.",
        "struct PlotNeed { int target; int rainfall; int retention_percent; };\nstruct WaterPlan { std::vector<int> applied; long long unmet; };",
        "std::optional<WaterPlan> irrigation_deficit_plan(const std::vector<PlotNeed>& plots, int budget)",
        """if(budget<0)return std::nullopt;WaterPlan out;long long unmet=0;for(const auto&p:plots){if(p.target<0||p.rainfall<0||p.retention_percent<0||p.retention_percent>100)return std::nullopt;long long retained=static_cast<long long>(p.rainfall)*p.retention_percent/100;long long need=std::max(0LL,static_cast<long long>(p.target)-retained);int give=static_cast<int>(std::min<long long>(need,budget));out.applied.push_back(give);budget-=give;unmet+=need-give;}out.unmet=unmet;return out;""",
        """auto r=irrigation_deficit_plan({{10,4,50},{5,5,100}},6);assert(r&&r->applied==(std::vector<int>{6,0})&&r->unmet==2);
    assert(irrigation_deficit_plan({},0)->applied.empty());
    assert(!irrigation_deficit_plan({},-1));
    assert(!irrigation_deficit_plan({{1,1,101}},0));
    assert(irrigation_deficit_plan({{0,9,50}},0)->unmet==0);""",
        ["budget and plot fields are nonnegative", "retention percentage is bounded", "integer retained rainfall rounds down", "allocation is stable by plot order", "unmet need includes every plot"],
        "stable capped allocation after integer retention calculation", ["irrigation", "allocation", "deficit"],
    )
    add(
        "Kindergarten Garden", "crop-compatibility-matching", "Crop compatibility matching",
        "Find the lexicographically smallest perfect assignment of distinct crops to named plots under allowed-pair constraints. Plots and crops are sorted unique nonempty lists. Unknown or duplicate pairs reject; return no assignment when unsatisfiable.",
        "struct AllowedCrop { std::string plot; std::string crop; };",
        "std::optional<std::optional<std::vector<std::pair<std::string,std::string>>>> match_crops(const std::vector<std::string>& plots, const std::vector<std::string>& crops, const std::vector<AllowedCrop>& allowed)",
        """auto canonical=[](const std::vector<std::string>&v){return std::is_sorted(v.begin(),v.end())&&std::adjacent_find(v.begin(),v.end())==v.end()&&std::find(v.begin(),v.end(),"")==v.end();};if(plots.size()!=crops.size()||!canonical(plots)||!canonical(crops))return std::nullopt;std::set<std::pair<std::string,std::string>> edges;for(const auto&a:allowed)if(!std::binary_search(plots.begin(),plots.end(),a.plot)||!std::binary_search(crops.begin(),crops.end(),a.crop)||!edges.emplace(a.plot,a.crop).second)return std::nullopt;std::vector<std::string> perm=crops;do{bool ok=true;for(std::size_t i=0;i<plots.size();++i)ok=ok&&edges.count({plots[i],perm[i]});if(ok){std::vector<std::pair<std::string,std::string>> out;for(std::size_t i=0;i<plots.size();++i)out.push_back({plots[i],perm[i]});return out;}}while(std::next_permutation(perm.begin(),perm.end()));return std::optional<std::vector<std::pair<std::string,std::string>>>{};""",
        """auto r=match_crops({"east","west"},{"bean","pea"},{{"east","pea"},{"west","bean"}});assert(r&&*r&&(**r)[0].second=="pea");
    auto e=match_crops({}, {}, {});assert(e&&*e&&(**e).empty());
    auto none=match_crops({"p"},{"c"},{});assert(none&&!*none);
    assert(!match_crops({"b","a"},{"c","d"},{}));
    assert(!match_crops({"p"},{"c"},{{"x","c"}}));""",
        ["plot and crop domains are sorted unique", "domain sizes must match", "allowed pairs are unique and known", "the lexical crop-vector assignment wins", "unsatisfiable is distinct from invalid"],
        "bounded lexicographic permutation search over a validated bipartite graph", ["matching", "lexicographic", "garden"],
    )
    add(
        "Kindergarten Garden", "harvest-conflict-colors", "Harvest conflict colors",
        "Color a crop conflict graph with at most a supplied number of harvest days, returning the lexicographically smallest day vector for sorted crop names. Conflicts are unique undirected non-self edges. Reject malformed graphs; distinguish unsatisfiable from invalid.",
        "struct CropConflict { std::string first; std::string second; };",
        "std::optional<std::optional<std::vector<int>>> harvest_conflict_colors(const std::vector<std::string>& crops, const std::vector<CropConflict>& conflicts, int days)",
        """if(days<0||!std::is_sorted(crops.begin(),crops.end())||std::adjacent_find(crops.begin(),crops.end())!=crops.end()||std::find(crops.begin(),crops.end(),"")!=crops.end())return std::nullopt;std::set<std::pair<int,int>> edges;for(const auto&e:conflicts){auto a=std::lower_bound(crops.begin(),crops.end(),e.first),b=std::lower_bound(crops.begin(),crops.end(),e.second);if(a==crops.end()||*a!=e.first||b==crops.end()||*b!=e.second||a==b)return std::nullopt;int x=static_cast<int>(a-crops.begin()),y=static_cast<int>(b-crops.begin());if(x>y)std::swap(x,y);if(!edges.insert({x,y}).second)return std::nullopt;}std::vector<int> color(crops.size());std::function<bool(std::size_t)> solve=[&](std::size_t i){if(i==crops.size())return true;for(int d=0;d<days;++d){bool ok=true;for(auto e:edges)if(e.second==static_cast<int>(i)&&color[e.first]==d)ok=false;if(ok){color[i]=d;if(solve(i+1))return true;}}return false;};if(solve(0))return color;return std::optional<std::vector<int>>{};""",
        """auto r=harvest_conflict_colors({"a","b","c"},{{"a","b"},{"b","c"}},2);assert(r&&*r&&**r==(std::vector<int>{0,1,0}));
    auto e=harvest_conflict_colors({}, {}, 0);assert(e&&*e&&(**e).empty());
    auto none=harvest_conflict_colors({"a","b"},{{"a","b"}},1);assert(none&&!*none);
    assert(!harvest_conflict_colors({"b","a"},{},2));
    assert(!harvest_conflict_colors({"a"},{{"a","a"}},2));""",
        ["crop domain is sorted unique", "conflicts are undirected unique and non-self", "days are zero-based", "lexicographically smallest color vector wins", "empty graph is satisfiable with zero days"],
        "ordered backtracking graph coloring with canonical edge validation", ["graph-coloring", "harvest", "constraint"],
    )

    add(
        "Linked List", "random-link-clone-map", "Random-link clone map",
        "Clone a linked record chain expressed by next and random indices into traversal order. Every reachable next index must be unique and terminate; random links may target only reachable nodes. Return remapped next/random indices and reject unreachable input records.",
        "struct LinkRecord { int value; int next; int random; };",
        "std::optional<std::vector<LinkRecord>> clone_random_chain(const std::vector<LinkRecord>& records, int head)",
        """auto index_ok=[&](int x){return x>=-1&&x<static_cast<int>(records.size());};if(!index_ok(head))return std::nullopt;for(const auto&r:records)if(!index_ok(r.next)||!index_ok(r.random))return std::nullopt;std::vector<int> order;std::map<int,int> remap;for(int cur=head;cur!=-1;cur=records[cur].next){if(remap.count(cur))return std::nullopt;remap[cur]=static_cast<int>(order.size());order.push_back(cur);}if(order.size()!=records.size())return std::nullopt;std::vector<LinkRecord> out;for(int old:order){const auto&r=records[old];if(r.random!=-1&&!remap.count(r.random))return std::nullopt;out.push_back({r.value,r.next==-1?-1:remap[r.next],r.random==-1?-1:remap[r.random]});}return out;""",
        """auto r=clone_random_chain({{9,-1,1},{4,0,0}},1);assert(r&&r->at(0).value==4&&r->at(0).next==1&&r->at(0).random==1&&r->at(1).random==0);
    assert(clone_random_chain({},-1)->empty());
    assert(!clone_random_chain({{1,0,-1}},0));
    assert(!clone_random_chain({{1,-1,-1},{2,-1,-1}},0));
    assert(!clone_random_chain({},0));""",
        ["all indices are -1 or in range", "next chain terminates without cycles", "every input record is reachable", "random links target reachable records", "output order follows next traversal"],
        "chain traversal builds an old-to-new index map for cross-link remapping", ["linked-record", "clone", "cross-link"],
    )
    add(
        "Linked List", "sorted-chain-kway-merge", "Sorted chain k-way merge",
        "Merge multiple individually nondecreasing integer chains into one nondecreasing chain while preserving chain index order on equal values. Reject any unsorted input chain and return the source chain index beside each value.",
        "struct OriginValue { int value; std::size_t chain; };",
        "std::optional<std::vector<OriginValue>> merge_sorted_chains(const std::vector<std::vector<int>>& chains)",
        """for(const auto&c:chains)if(!std::is_sorted(c.begin(),c.end()))return std::nullopt;using Item=std::tuple<int,std::size_t,std::size_t>;std::priority_queue<Item,std::vector<Item>,std::greater<Item>> heap;for(std::size_t i=0;i<chains.size();++i)if(!chains[i].empty())heap.emplace(chains[i][0],i,0);std::vector<OriginValue> out;while(!heap.empty()){auto[value,chain,index]=heap.top();heap.pop();out.push_back({value,chain});if(index+1<chains[chain].size())heap.emplace(chains[chain][index+1],chain,index+1);}return out;""",
        """auto r=merge_sorted_chains({{1,3},{1,2},{}});assert(r&&r->size()==4&&r->at(0).chain==0&&r->at(1).chain==1&&r->at(3).value==3);
    assert(merge_sorted_chains({})->empty());
    assert(merge_sorted_chains({{}})->empty());
    assert(!merge_sorted_chains({{2,1}}));""",
        ["each source chain is nondecreasing", "empty sources are allowed", "equal values order by source chain then source position", "output records retain origin", "all values are preserved"],
        "priority-queue k-way merge with a composite stable tie key", ["k-way-merge", "chain", "stable-tie"],
    )
    add(
        "Linked List", "splice-command-replay", "Splice command replay",
        "Replay move-after commands over a unique integer chain. Each command removes one existing value and inserts it after another existing distinct value, or at the head using no anchor. Return the final order; reject missing values, self anchors, or duplicate initial values.",
        "struct MoveAfter { int value; std::optional<int> anchor; };",
        "std::optional<std::vector<int>> replay_splices(const std::vector<int>& initial, const std::vector<MoveAfter>& commands)",
        """std::vector<int> order=initial;std::set<int> unique(order.begin(),order.end());if(unique.size()!=order.size())return std::nullopt;for(const auto&cmd:commands){if(!unique.count(cmd.value)||(cmd.anchor&&(!unique.count(*cmd.anchor)||*cmd.anchor==cmd.value)))return std::nullopt;auto it=std::find(order.begin(),order.end(),cmd.value);order.erase(it);if(!cmd.anchor)order.insert(order.begin(),cmd.value);else{auto anchor=std::find(order.begin(),order.end(),*cmd.anchor);order.insert(anchor+1,cmd.value);}}return order;""",
        """assert(replay_splices({1,2,3},{{1,3},{3,std::nullopt}}).value()==(std::vector<int>{3,2,1}));
    assert(replay_splices({},{})->empty());
    assert(!replay_splices({1,1},{}));
    assert(!replay_splices({1},{{2,std::nullopt}}));
    assert(!replay_splices({1},{{1,1}}));""",
        ["initial values are unique", "command values and anchors must exist", "self anchoring rejects", "head insertion uses empty anchor", "commands observe results of earlier commands"],
        "ordered-vector simulation of remove-and-reinsert list operations", ["splice", "command-replay", "linked-order"],
    )

    add(
        "Parallel Letter Frequency", "parallel-anagram-buckets", "Parallel anagram buckets",
        "Group words by ASCII-letter anagram signature using at most worker_count asynchronous shards. Comparison ignores ASCII case and nonletters, but output preserves original words and stable input order within groups. Groups sort by signature.",
        "struct AnagramBucket { std::array<int,26> signature; std::vector<std::string> words; };",
        "std::optional<std::vector<AnagramBucket>> parallel_anagram_buckets(const std::vector<std::string>& words, std::size_t worker_count)",
        """if(worker_count==0)return std::nullopt;worker_count=std::min(worker_count,std::max<std::size_t>(1,words.size()));using Map=std::map<std::array<int,26>,std::vector<std::pair<std::size_t,std::string>>>;std::vector<std::future<Map>> jobs;for(std::size_t w=0;w<worker_count;++w)jobs.push_back(std::async(std::launch::async,[&,w]{Map m;for(std::size_t i=w;i<words.size();i+=worker_count){std::array<int,26>s{};for(unsigned char c:words[i])if(std::isalpha(c)&&c<128)++s[static_cast<std::size_t>(std::tolower(c)-'a')];m[s].push_back({i,words[i]});}return m;}));Map merged;for(auto&job:jobs)for(auto&entry:job.get())merged[entry.first].insert(merged[entry.first].end(),entry.second.begin(),entry.second.end());std::vector<AnagramBucket> out;for(auto&entry:merged){std::sort(entry.second.begin(),entry.second.end());AnagramBucket b{entry.first,{}};for(auto&word:entry.second)b.words.push_back(word.second);out.push_back(std::move(b));}return out;""",
        """auto r=parallel_anagram_buckets({"Tea","eat","dog"},2);assert(r&&r->size()==2);std::size_t total=0;for(const auto&b:*r)total+=b.words.size();assert(total==3);
    assert(parallel_anagram_buckets({},3)->empty());
    assert(!parallel_anagram_buckets({},0));
    auto q=parallel_anagram_buckets({"a!","A"},8);assert(q&&q->size()==1&&q->at(0).words[0]=="a!");""",
        ["worker count must be positive", "worker count above input size is bounded", "only ASCII letters form signatures", "original word bytes are preserved", "group and within-group order are deterministic"],
        "strided asynchronous signature maps merged with original indices", ["parallel", "anagram", "deterministic-merge"],
    )
    add(
        "Parallel Letter Frequency", "parallel-vowel-gap-histogram", "Parallel vowel gap histogram",
        "Across multiple texts, count distances between consecutive ASCII vowels within each text, case-insensitively. Process texts in bounded asynchronous shards and merge into a sorted distance histogram. Nonletters do not reset the absolute byte distance.",
        "",
        "std::optional<std::map<std::size_t,std::size_t>> parallel_vowel_gap_histogram(const std::vector<std::string>& texts, std::size_t worker_count)",
        """if(worker_count==0)return std::nullopt;worker_count=std::min(worker_count,std::max<std::size_t>(1,texts.size()));std::vector<std::future<std::map<std::size_t,std::size_t>>> jobs;for(std::size_t w=0;w<worker_count;++w)jobs.push_back(std::async(std::launch::async,[&,w]{std::map<std::size_t,std::size_t> local;for(std::size_t t=w;t<texts.size();t+=worker_count){std::optional<std::size_t> last;for(std::size_t i=0;i<texts[t].size();++i){unsigned char c=texts[t][i];char low=c<128?static_cast<char>(std::tolower(c)):'?';if(std::string("aeiou").find(low)!=std::string::npos){if(last)++local[i-*last];last=i;}}}return local;}));std::map<std::size_t,std::size_t> out;for(auto&job:jobs)for(auto item:job.get())out[item.first]+=item.second;return out;""",
        """auto r=parallel_vowel_gap_histogram({"a--E-i","bbb","OU"},2);assert(r&&r->at(3)==1&&r->at(2)==1&&r->at(1)==1);
    assert(parallel_vowel_gap_histogram({},1)->empty());
    assert(!parallel_vowel_gap_histogram({},0));
    assert(parallel_vowel_gap_histogram({"x"},4)->empty());""",
        ["worker count must be positive", "vowel state resets between texts", "byte positions define distance", "ASCII case is ignored", "merged histogram keys are ascending"],
        "per-text vowel-position scan in asynchronous strided shards", ["parallel", "histogram", "vowel-distance"],
    )
    add(
        "Parallel Letter Frequency", "ordered-shard-checksum", "Ordered shard checksum",
        "Compute a deterministic polynomial checksum of ASCII letters as if all texts were concatenated in input order, while analyzing bounded contiguous shards asynchronously. Nonletters are skipped and case is folded; modulus must exceed one.",
        "",
        "std::optional<std::uint64_t> parallel_ordered_checksum(const std::vector<std::string>& texts, std::size_t workers, std::uint64_t modulus)",
        """if(workers==0||modulus<=1)return std::nullopt;workers=std::min(workers,std::max<std::size_t>(1,texts.size()));struct Part{std::uint64_t hash;std::size_t letters;};std::vector<std::future<Part>> jobs;for(std::size_t w=0;w<workers;++w){std::size_t lo=texts.size()*w/workers,hi=texts.size()*(w+1)/workers;jobs.push_back(std::async(std::launch::async,[&,lo,hi]{Part p{0,0};for(std::size_t i=lo;i<hi;++i)for(unsigned char c:texts[i])if(c<128&&std::isalpha(c)){p.hash=(p.hash*257+static_cast<unsigned char>(std::tolower(c)))%modulus;++p.letters;}return p;}));}std::uint64_t out=0;for(auto&job:jobs){Part p=job.get();for(std::size_t i=0;i<p.letters;++i)out=(out*257)%modulus;out=(out+p.hash)%modulus;}return out;""",
        """auto serial=parallel_ordered_checksum({"Ab!","c"},1,1000003);auto parallel=parallel_ordered_checksum({"Ab!","c"},3,1000003);assert(serial&&parallel&&serial==parallel);
    assert(parallel_ordered_checksum({},4,7)==0);
    assert(!parallel_ordered_checksum({},0,7));
    assert(!parallel_ordered_checksum({},1,1));""",
        ["workers and modulus are validated", "only ASCII letters participate", "case folding is deterministic", "concatenation order is preserved across shards", "empty input checksum is zero"],
        "contiguous shard polynomial summaries combined by exponent shifting", ["parallel", "checksum", "ordered-reduction"],
    )

    add(
        "Phone Number", "e164-country-split", "E.164 country split",
        "Normalize an international number containing spaces, hyphens, and parentheses, then split it using the longest matching sorted unique country-code prefix. Input must begin with plus and contain 8 through 15 digits; subscriber number may not begin with zero.",
        "struct InternationalNumber { std::string country_code; std::string subscriber; };",
        "std::optional<InternationalNumber> split_e164(std::string_view text, const std::vector<std::string>& country_codes)",
        """if(text.empty()||text.front()!='+')return std::nullopt;std::string digits;for(std::size_t i=1;i<text.size();++i){unsigned char c=text[i];if(std::isdigit(c))digits.push_back(static_cast<char>(c));else if(c!=' '&&c!='-'&&c!='('&&c!=')')return std::nullopt;}if(digits.size()<8||digits.size()>15||digits.front()=='0')return std::nullopt;if(!std::is_sorted(country_codes.begin(),country_codes.end())||std::adjacent_find(country_codes.begin(),country_codes.end())!=country_codes.end())return std::nullopt;std::string best;for(const auto&code:country_codes){if(code.empty()||code.size()>3||code.front()=='0'||!std::all_of(code.begin(),code.end(),[](unsigned char c){return std::isdigit(c);}))return std::nullopt;if(digits.rfind(code,0)==0&&code.size()>best.size())best=code;}if(best.empty()||best.size()==digits.size()||digits[best.size()]=='0')return std::nullopt;return InternationalNumber{best,digits.substr(best.size())};""",
        """auto r=split_e164("+1 (212) 555-0100",{"1","12","44"});assert(r&&r->country_code=="12"&&r->subscriber=="125550100");
    assert(!split_e164("12125550100",{"1"}));
    assert(!split_e164("+01234567",{"1"}));
    assert(!split_e164("+12125550100",{"12","1"}));
    assert(!split_e164("+12000000",{"1","12"}));""",
        ["leading plus is mandatory", "only defined separators are ignored", "digit length is E.164 bounded", "country code table is sorted unique and well formed", "longest prefix wins and subscriber begins nonzero"],
        "strict normalization followed by longest validated prefix selection", ["e164", "normalization", "prefix"],
    )
    add(
        "Phone Number", "t9-predictive-ranking", "T9 predictive ranking",
        "Rank dictionary words matching an exact T9 digit string. Words contain only ASCII letters; comparison is case-insensitive, then higher frequency, then lowercase lexical word, then original index. Reject malformed digits, words, or negative frequencies.",
        "struct RankedWord { std::string word; int frequency; };",
        "std::optional<std::vector<std::string>> t9_rank(std::string_view digits, const std::vector<RankedWord>& dictionary)",
        """if(!std::all_of(digits.begin(),digits.end(),[](char c){return c>='2'&&c<='9';}))return std::nullopt;auto key=[](char c){c=static_cast<char>(std::tolower(static_cast<unsigned char>(c)));const std::array<std::string,8> g={"abc","def","ghi","jkl","mno","pqrs","tuv","wxyz"};for(std::size_t i=0;i<g.size();++i)if(g[i].find(c)!=std::string::npos)return static_cast<char>('2'+i);return '?';};struct Item{int f;std::string low;std::size_t i;std::string original;};std::vector<Item> items;for(std::size_t i=0;i<dictionary.size();++i){const auto&w=dictionary[i];if(w.frequency<0||w.word.size()!=digits.size()||!std::all_of(w.word.begin(),w.word.end(),[](unsigned char c){return c<128&&std::isalpha(c);}))return std::nullopt;std::string encoded,low;for(char c:w.word){encoded.push_back(key(c));low.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(c))));}if(encoded==digits)items.push_back({w.frequency,low,i,w.word});}std::sort(items.begin(),items.end(),[](const auto&a,const auto&b){if(a.f!=b.f)return a.f>b.f;if(a.low!=b.low)return a.low<b.low;return a.i<b.i;});std::vector<std::string> out;for(auto&x:items)out.push_back(x.original);return out;""",
        """auto r=t9_rank("228",{{"cat",4},{"bat",7},{"act",7}});assert(r&&*r==(std::vector<std::string>{"act","bat","cat"}));
    assert(t9_rank("",{})->empty());
    assert(!t9_rank("10",{}));
    assert(!t9_rank("2",{{"a!",1}}));
    assert(!t9_rank("2",{{"a",-1}}));""",
        ["digits use only 2 through 9", "all dictionary words are exact length ASCII letters", "only matching encodings are returned", "frequency sorts descending", "lowercase lexical and original index break ties"],
        "validated T9 projection followed by deterministic multi-key ranking", ["t9", "ranking", "phone"],
    )
    add(
        "Phone Number", "overlap-call-billing", "Overlap call billing",
        "Bill the union of half-open call intervals per normalized number, applying a constant cents-per-minute rate and rounding each merged interval up to whole minutes. Reject invalid numbers, intervals, rates, or total overflow; return numbers sorted.",
        "struct CallSpan { std::string number; int begin_second; int end_second; };",
        "std::optional<std::map<std::string,long long>> bill_call_unions(const std::vector<CallSpan>& calls, int cents_per_minute)",
        """if(cents_per_minute<0)return std::nullopt;std::map<std::string,std::vector<std::pair<int,int>>> by;for(const auto&c:calls){if(c.number.empty()||!std::all_of(c.number.begin(),c.number.end(),[](unsigned char x){return std::isdigit(x);})||c.begin_second<0||c.end_second<c.begin_second)return std::nullopt;by[c.number].push_back({c.begin_second,c.end_second});}std::map<std::string,long long> out;for(auto&entry:by){auto&v=entry.second;std::sort(v.begin(),v.end());long long cost=0;int begin=0,end=0;bool active=false;auto charge=[&](int a,int b){long long minutes=(static_cast<long long>(b)-a+59)/60;if(minutes&&cost>LLONG_MAX-minutes*cents_per_minute)return false;cost+=minutes*cents_per_minute;return true;};for(auto p:v){if(!active){begin=p.first;end=p.second;active=true;}else if(p.first<=end)end=std::max(end,p.second);else{if(!charge(begin,end))return std::nullopt;begin=p.first;end=p.second;}}if(active&&!charge(begin,end))return std::nullopt;out[entry.first]=cost;}return out;""",
        """auto r=bill_call_unions({{"12",0,61},{"12",60,120},{"34",0,0}},5);assert(r&&r->at("12")==10&&r->at("34")==0);
    assert(bill_call_unions({},3)->empty());
    assert(!bill_call_unions({{"",0,1}},1));
    assert(!bill_call_unions({{"1",2,1}},1));
    assert(!bill_call_unions({},-1));""",
        ["numbers contain digits only", "intervals are nonnegative half-open", "overlapping and touching intervals merge", "each merged interval rounds independently", "cost arithmetic is checked"],
        "per-number interval union followed by checked rounded-duration billing", ["billing", "interval-union", "phone"],
    )

    add(
        "Spiral Matrix", "hex-spiral-coordinate", "Hex spiral coordinate",
        "Map a nonnegative index to axial coordinates on an outward hexagonal spiral. Index zero is the origin; each ring begins at (ring,0) and walks six fixed axial directions counterclockwise. Reject indices above a caller bound.",
        "struct Axial { long long q; long long r; };",
        "std::optional<Axial> hex_spiral_coordinate(std::uint64_t index, std::uint64_t maximum)",
        """if(index>maximum)return std::nullopt;if(index==0)return Axial{0,0};std::uint64_t ring=1,start=1;while(index>=start+6*ring){start+=6*ring;++ring;}long long q=static_cast<long long>(ring),r=0;const std::array<Axial,6> dirs={Axial{0,-1},Axial{-1,0},Axial{-1,1},Axial{0,1},Axial{1,0},Axial{1,-1}};std::uint64_t offset=index-start;for(const auto&d:dirs){std::uint64_t step=std::min(offset,ring);q+=d.q*static_cast<long long>(step);r+=d.r*static_cast<long long>(step);offset-=step;if(offset==0)break;}return Axial{q,r};""",
        """auto a=hex_spiral_coordinate(0,20);assert(a&&a->q==0&&a->r==0);auto b=hex_spiral_coordinate(1,20);assert(b&&b->q==1&&b->r==0);auto c=hex_spiral_coordinate(6,20);assert(c&&c->q==0&&c->r==1);auto d=hex_spiral_coordinate(7,20);assert(d&&d->q==2&&d->r==0);
    assert(!hex_spiral_coordinate(2,1));""",
        ["index zero is the origin", "ring starts are deterministic", "six axial direction order is fixed", "caller maximum is inclusive", "coordinates use signed 64-bit values"],
        "ring localization followed by at most six axial segment advances", ["hex-grid", "spiral", "coordinate"],
    )
    add(
        "Spiral Matrix", "spiral-permutation-cycles", "Spiral permutation cycles",
        "For a rectangular matrix, derive the permutation from row-major positions to clockwise spiral-read positions and return its disjoint cycles of length greater than one. Each cycle starts at its smallest index and cycles sort by first index.",
        "",
        "std::optional<std::vector<std::vector<std::size_t>>> spiral_permutation_cycles(std::size_t rows, std::size_t columns, std::size_t maximum_cells)",
        """if(columns&&rows>maximum_cells/columns)return std::nullopt;const std::size_t n=rows*columns;if(n>maximum_cells||rows>static_cast<std::size_t>(LLONG_MAX)||columns>static_cast<std::size_t>(LLONG_MAX))return std::nullopt;std::vector<std::size_t> order;if(n){long long top=0,left=0,bottom=static_cast<long long>(rows)-1,right=static_cast<long long>(columns)-1;while(top<=bottom&&left<=right){for(long long c=left;c<=right;++c)order.push_back(static_cast<std::size_t>(top)*columns+static_cast<std::size_t>(c));++top;for(long long r=top;r<=bottom;++r)order.push_back(static_cast<std::size_t>(r)*columns+static_cast<std::size_t>(right));--right;if(top<=bottom){for(long long c=right;c>=left;--c)order.push_back(static_cast<std::size_t>(bottom)*columns+static_cast<std::size_t>(c));--bottom;}if(left<=right){for(long long r=bottom;r>=top;--r)order.push_back(static_cast<std::size_t>(r)*columns+static_cast<std::size_t>(left));++left;}}}std::vector<std::size_t> perm(n);for(std::size_t i=0;i<n;++i)perm[order[i]]=i;std::vector<bool> seen(n);std::vector<std::vector<std::size_t>> out;for(std::size_t i=0;i<n;++i)if(!seen[i]){std::vector<std::size_t> cycle;for(std::size_t x=i;!seen[x];x=perm[x]){seen[x]=true;cycle.push_back(x);}if(cycle.size()>1)out.push_back(cycle);}return out;""",
        """auto r=spiral_permutation_cycles(2,3,6);assert(r&&r->size()==1&&r->at(0)==(std::vector<std::size_t>{3,5}));
    assert(spiral_permutation_cycles(1,4,4)->empty());
    assert(spiral_permutation_cycles(0,9,0)->empty());
    assert(!spiral_permutation_cycles(3,3,8));""",
        ["cell count is checked against maximum", "empty dimensions produce no cycles", "fixed points are omitted", "cycle discovery starts at the least unseen index", "clockwise spiral starts at top-left"],
        "spiral traversal inversion followed by canonical permutation cycle decomposition", ["permutation", "cycles", "spiral"],
    )
    add(
        "Spiral Matrix", "spiral-maze-route-validator", "Spiral maze route validator",
        "Validate a route through a rectangular blocked grid. The route must start at top-left, finish at bottom-right, visit each open cell exactly once, use orthogonal steps, and turn only in clockwise direction order right/down/left/up. Empty grids are invalid.",
        "struct Cell { int row; int column; };",
        "bool validate_clockwise_spiral_route(const std::vector<std::vector<bool>>& blocked, const std::vector<Cell>& route)",
        """if(blocked.empty()||blocked[0].empty())return false;const int rows=static_cast<int>(blocked.size()),cols=static_cast<int>(blocked[0].size());for(const auto&row:blocked)if(static_cast<int>(row.size())!=cols)return false;std::size_t open=0;for(const auto&row:blocked)for(bool b:row)if(!b)++open;if(route.size()!=open||route.empty()||route.front().row!=0||route.front().column!=0||route.back().row!=rows-1||route.back().column!=cols-1)return false;std::set<std::pair<int,int>> seen;int previous_direction=-1;for(std::size_t i=0;i<route.size();++i){const auto c=route[i];if(c.row<0||c.row>=rows||c.column<0||c.column>=cols||blocked[c.row][c.column]||!seen.insert({c.row,c.column}).second)return false;if(i){int dr=c.row-route[i-1].row,dc=c.column-route[i-1].column,dir=-1;if(dr==0&&dc==1)dir=0;else if(dr==1&&dc==0)dir=1;else if(dr==0&&dc==-1)dir=2;else if(dr==-1&&dc==0)dir=3;else return false;if(previous_direction!=-1&&dir!=previous_direction&&dir!=(previous_direction+1)%4)return false;previous_direction=dir;}}return true;""",
        """assert(validate_clockwise_spiral_route({{false,false},{true,false}},{{0,0},{0,1},{1,1}}));
    assert(!validate_clockwise_spiral_route({},{}));
    assert(!validate_clockwise_spiral_route({{false,false},{false,false}},{{0,0},{1,0},{1,1},{0,1}}));
    assert(!validate_clockwise_spiral_route({{false}},{}));
    assert(!validate_clockwise_spiral_route({{true}},{{0,0}}));""",
        ["grid is nonempty rectangular", "route covers each open cell exactly once", "fixed endpoints are required", "steps are orthogonal", "direction changes advance clockwise by one quarter-turn"],
        "complete route coverage and direction-state validation", ["maze", "route", "near-correct"],
    )

    add(
        "Sublist", "rectangular-submatrix-matches", "Rectangular submatrix matches",
        "Return every row/column origin where a rectangular integer pattern occurs exactly in a rectangular haystack, in row-major origin order. Empty pattern matches every boundary origin; reject ragged input matrices.",
        "struct MatrixOrigin { std::size_t row; std::size_t column; };",
        "std::optional<std::vector<MatrixOrigin>> submatrix_matches(const std::vector<std::vector<int>>& haystack, const std::vector<std::vector<int>>& pattern)",
        """auto width=[](const std::vector<std::vector<int>>&m)->std::optional<std::size_t>{std::size_t w=m.empty()?0:m[0].size();for(const auto&r:m)if(r.size()!=w)return std::nullopt;return w;};auto hw=width(haystack),pw=width(pattern);if(!hw||!pw)return std::nullopt;std::vector<MatrixOrigin> out;if(pattern.empty()){for(std::size_t r=0;r<=haystack.size();++r)for(std::size_t c=0;c<=*hw;++c)out.push_back({r,c});return out;}if(pattern.size()>haystack.size()||*pw>*hw)return out;for(std::size_t r=0;r+pattern.size()<=haystack.size();++r)for(std::size_t c=0;c+*pw<=*hw;++c){bool ok=true;for(std::size_t i=0;i<pattern.size();++i)for(std::size_t j=0;j<*pw;++j)ok=ok&&haystack[r+i][c+j]==pattern[i][j];if(ok)out.push_back({r,c});}return out;""",
        """auto r=submatrix_matches({{1,2,1},{3,4,3}},{{1},{3}});assert(r&&r->size()==2&&r->at(1).column==2);
    assert(submatrix_matches({},{})->size()==1);
    assert(submatrix_matches({{1,2}},{})->size()==6);
    assert(submatrix_matches({{1}},{{2}})->empty());
    assert(!submatrix_matches({{1},{1,2}},{{1}}));""",
        ["both matrices are rectangular", "origins sort row-major", "empty pattern matches boundary grid", "oversized pattern has no matches", "matching is exact"],
        "bounded row-major origin enumeration with exact rectangular comparison", ["submatrix", "matching", "2d"],
    )
    add(
        "Sublist", "bounded-edit-window", "Bounded edit window",
        "Find the earliest shortest contiguous haystack window whose Levenshtein distance from a pattern is at most a bound. Window length is restricted to pattern length plus or minus the bound. Reject negative bound; return no window when none qualifies.",
        "struct EditWindow { std::size_t begin; std::size_t count; int distance; };",
        "std::optional<std::optional<EditWindow>> bounded_edit_window(const std::vector<int>& haystack, const std::vector<int>& pattern, int bound)",
        """if(bound<0)return std::nullopt;std::optional<EditWindow> best;const std::size_t min_len=pattern.size()>static_cast<std::size_t>(bound)?pattern.size()-bound:0,max_len=pattern.size()+bound;for(std::size_t begin=0;begin<=haystack.size();++begin)for(std::size_t len=min_len;len<=max_len&&begin+len<=haystack.size();++len){std::vector<int> prev(pattern.size()+1),cur(pattern.size()+1);std::iota(prev.begin(),prev.end(),0);for(std::size_t i=1;i<=len;++i){cur[0]=static_cast<int>(i);for(std::size_t j=1;j<=pattern.size();++j)cur[j]=std::min({cur[j-1]+1,prev[j]+1,prev[j-1]+(haystack[begin+i-1]!=pattern[j-1])});prev.swap(cur);}int d=prev.back();if(d<=bound&&(!best||len<best->count||(len==best->count&&begin<best->begin)))best=EditWindow{begin,len,d};}return best;""",
        """auto r=bounded_edit_window({9,1,3,4},{1,2,3},1);assert(r&&*r&&(**r).begin==1&&(**r).count==2);
    auto e=bounded_edit_window({}, {}, 0);assert(e&&*e&&(**e).count==0);
    auto none=bounded_edit_window({1},{9,9},0);assert(none&&!*none);
    assert(!bounded_edit_window({}, {}, -1));""",
        ["bound is nonnegative", "candidate lengths are tightly bounded", "Levenshtein insertion deletion and substitution cost one", "shortest window wins before earliest origin", "invalid and no-match are distinct"],
        "bounded window enumeration with rolling-row edit distance", ["edit-distance", "window", "nested-result"],
    )
    add(
        "Sublist", "streaming-wildcard-ends", "Streaming wildcard ends",
        "Feed chunks into a fixed integer pattern containing an optional wildcard value and return absolute end offsets for matches completed by each feed. Overlapping matches are retained and empty pattern matches every stream boundary exactly once.",
        """class WildcardStreamMatcher {
public:
    explicit WildcardStreamMatcher(std::vector<std::optional<int>> pattern) : pattern_(std::move(pattern)) {}
    std::vector<std::size_t> feed(const std::vector<int>& chunk) {
        std::vector<std::size_t> ends;
        if (pattern_.empty() && !emitted_initial_) { ends.push_back(consumed_); emitted_initial_ = true; }
        for (int value : chunk) {
            tail_.push_back(value); ++consumed_;
            if (pattern_.empty()) { ends.push_back(consumed_); continue; }
            if (tail_.size() > pattern_.size()) tail_.erase(tail_.begin());
            if (tail_.size() == pattern_.size()) {
                bool match = true;
                for (std::size_t i=0;i<pattern_.size();++i) match = match && (!pattern_[i] || *pattern_[i] == tail_[i]);
                if (match) ends.push_back(consumed_);
            }
        }
        return ends;
    }
private:
    std::vector<std::optional<int>> pattern_;
    std::vector<int> tail_;
    std::size_t consumed_=0;
    bool emitted_initial_=false;
};""",
        "std::vector<std::size_t> wildcard_stream_demo(const std::vector<std::optional<int>>& pattern, const std::vector<std::vector<int>>& chunks)",
        """WildcardStreamMatcher matcher(pattern);std::vector<std::size_t> out;for(const auto&chunk:chunks){auto ends=matcher.feed(chunk);out.insert(out.end(),ends.begin(),ends.end());}return out;""",
        """auto r=wildcard_stream_demo({1,std::nullopt,1},{{1,2},{1,3,1}});assert(r==(std::vector<std::size_t>{3,5}));
    auto e=wildcard_stream_demo({},{{},{7,8}});assert(e==(std::vector<std::size_t>{0,1,2}));
    assert(wildcard_stream_demo({9},{{1},{9}})==(std::vector<std::size_t>{2}));""",
        ["chunks may be empty", "absolute end offsets count consumed elements", "overlapping matches are returned", "wildcard matches exactly one value", "empty pattern emits each boundary once"],
        "stream-history matching with absolute boundary accounting", ["streaming", "wildcard", "overlap"],
    )

    add(
        "Yacht", "reroll-sum-distribution", "Reroll sum distribution",
        "Return the exact count distribution of final sums after rerolling selected dice once. Kept dice are fixed; each rerolled die ranges from one through sides independently. Reject invalid sides, die values, reroll indices, duplicates, or a state-space bound breach.",
        "",
        "std::optional<std::map<int,std::uint64_t>> reroll_sum_distribution(const std::vector<int>& dice, int sides, const std::vector<std::size_t>& reroll, std::uint64_t maximum_outcomes)",
        """if(sides<=0)return std::nullopt;for(int d:dice)if(d<1||d>sides)return std::nullopt;std::set<std::size_t> chosen;for(auto i:reroll)if(i>=dice.size()||!chosen.insert(i).second)return std::nullopt;std::uint64_t outcomes=1;for(std::size_t i=0;i<reroll.size();++i){if(outcomes>maximum_outcomes/static_cast<std::uint64_t>(sides))return std::nullopt;outcomes*=sides;}std::map<int,std::uint64_t> dist;int kept=0;for(std::size_t i=0;i<dice.size();++i)if(!chosen.count(i))kept+=dice[i];std::function<void(std::size_t,int)> rec=[&](std::size_t k,int sum){if(k==reroll.size()){++dist[sum];return;}for(int face=1;face<=sides;++face)rec(k+1,sum+face);};rec(0,kept);return dist;""",
        """auto r=reroll_sum_distribution({1,6},6,{0},6);assert(r&&r->size()==6&&r->at(7)==1&&r->at(12)==1);
    assert(reroll_sum_distribution({2},6,{},1).value()==(std::map<int,std::uint64_t>{{2,1}}));
    assert(!reroll_sum_distribution({0},6,{},1));
    assert(!reroll_sum_distribution({1},6,{0,0},6));
    assert(!reroll_sum_distribution({1,1},6,{0,1},35));""",
        ["die faces and sides are validated", "reroll indices are unique and in range", "kept dice remain fixed", "outcome counts are exact", "state-space maximum is enforced before enumeration"],
        "bounded recursive convolution of independent rerolled faces", ["dice", "distribution", "exact-count"],
    )
    add(
        "Yacht", "target-hold-choice", "Target hold choice",
        "Choose which dice to hold to maximize the number of one-reroll outcomes whose final sum equals a target. Ties prefer more held dice, then the lexicographically smaller held-index vector. Reject invalid dice or excessive enumeration.",
        "struct HoldChoice { std::vector<std::size_t> held; std::uint64_t winning_outcomes; std::uint64_t total_outcomes; };",
        "std::optional<HoldChoice> best_target_hold(const std::vector<int>& dice, int sides, int target, std::uint64_t maximum_outcomes)",
        """if(sides<=0||dice.size()>20)return std::nullopt;for(int d:dice)if(d<1||d>sides)return std::nullopt;std::optional<HoldChoice> best;const std::uint64_t masks=std::uint64_t{1}<<dice.size();for(std::uint64_t mask=0;mask<masks;++mask){std::vector<std::size_t> held;int fixed=0;std::size_t free=0;for(std::size_t i=0;i<dice.size();++i)if(mask&(std::uint64_t{1}<<i)){held.push_back(i);fixed+=dice[i];}else ++free;std::uint64_t total=1;for(std::size_t i=0;i<free;++i){if(total>maximum_outcomes/static_cast<std::uint64_t>(sides))return std::nullopt;total*=sides;}std::uint64_t wins=0;std::function<void(std::size_t,int)> rec=[&](std::size_t k,int sum){if(k==free){wins+=sum==target;return;}for(int f=1;f<=sides;++f)rec(k+1,sum+f);};rec(0,fixed);if(!best||wins*best->total_outcomes>best->winning_outcomes*total||(wins*best->total_outcomes==best->winning_outcomes*total&&(held.size()>best->held.size()||(held.size()==best->held.size()&&held<best->held))))best=HoldChoice{held,wins,total};}return best;""",
        """auto r=best_target_hold({6,1},6,12,100);assert(r&&r->held==(std::vector<std::size_t>{0})&&r->winning_outcomes==1&&r->total_outcomes==6);
    auto e=best_target_hold({},6,0,10);assert(e&&e->held.empty()&&e->winning_outcomes==1);
    assert(!best_target_hold({0},6,4,10));
    assert(!best_target_hold({1,1},6,7,5));""",
        ["all dice and sides are validated", "every hold subset is considered", "win probability compares exact fractions", "ties prefer more held dice then lexical indices", "enumeration limit applies to every candidate"],
        "exhaustive hold-subset search with exact outcome enumeration and deterministic ties", ["dice", "optimization", "near-correct"],
    )
    add(
        "Yacht", "scorecard-category-matching", "Scorecard category matching",
        "Assign distinct dice rolls to distinct declared scoring categories to maximize total score. Unknown category names or malformed rolls reject. Return the lexicographically smallest category-index vector among optimal assignments; unused rolls are allowed.",
        "struct ScoreAssignment { int total; std::vector<int> category_for_roll; };",
        "std::optional<ScoreAssignment> optimize_scorecard(const std::vector<std::vector<int>>& rolls, const std::vector<std::string>& categories)",
        """std::set<std::string> allowed={"sum","pairs","triples"},unique;for(const auto&c:categories)if(!allowed.count(c)||!unique.insert(c).second)return std::nullopt;for(const auto&r:rolls)if(r.empty()||!std::all_of(r.begin(),r.end(),[](int d){return d>=1&&d<=6;}))return std::nullopt;ScoreAssignment best{-1,{}};std::vector<int> assignment(rolls.size(),-1);std::vector<bool> used(categories.size());std::function<void(std::size_t,int)> rec=[&](std::size_t i,int total){if(i==rolls.size()){if(total>best.total||(total==best.total&&assignment<best.category_for_roll))best={total,assignment};return;}rec(i+1,total);std::map<int,int> count;int sum=0;for(int d:rolls[i]){++count[d];sum+=d;}for(std::size_t c=0;c<categories.size();++c)if(!used[c]){int score=0;if(categories[c]=="sum")score=sum;else if(categories[c]=="pairs")for(auto x:count)if(x.second>=2)score=std::max(score,2*x.first);else{}else for(auto x:count)if(x.second>=3)score=std::max(score,3*x.first);used[c]=true;assignment[i]=static_cast<int>(c);rec(i+1,total+score);assignment[i]=-1;used[c]=false;}};rec(0,0);return best;""",
        """auto r=optimize_scorecard({{6,6,1},{3,3,3}},{"pairs","triples"});assert(r&&r->total==21&&r->category_for_roll==(std::vector<int>{0,1}));
    assert(optimize_scorecard({},{})->total==0);
    assert(!optimize_scorecard({{0}},{"sum"}));
    assert(!optimize_scorecard({{1}},{"mystery"}));
    assert(!optimize_scorecard({{1}},{"sum","sum"}));""",
        ["rolls are nonempty valid dice", "category names are unique and declared", "each category and roll is used at most once", "unused rolls use -1", "optimal ties choose lexical assignment vector"],
        "backtracking bipartite score assignment with deterministic optimal tie break", ["scorecard", "matching", "optimization"],
    )

    add(
        "Zebra Puzzle", "exact-cover-solution-count", "Exact cover solution count",
        "Count exact covers of a sorted unique universe using uniquely named sorted unique subsets. Every universe value must be known and each selected subset must cover disjoint values. Stop and reject when a caller count limit would be exceeded.",
        "struct NamedSubset { std::string name; std::vector<int> values; };",
        "std::optional<std::size_t> exact_cover_count(const std::vector<int>& universe, const std::vector<NamedSubset>& subsets, std::size_t maximum_count)",
        """if(!std::is_sorted(universe.begin(),universe.end())||std::adjacent_find(universe.begin(),universe.end())!=universe.end())return std::nullopt;std::set<std::string> names;for(const auto&s:subsets)if(s.name.empty()||!names.insert(s.name).second||!std::is_sorted(s.values.begin(),s.values.end())||std::adjacent_find(s.values.begin(),s.values.end())!=s.values.end()||!std::all_of(s.values.begin(),s.values.end(),[&](int v){return std::binary_search(universe.begin(),universe.end(),v);}))return std::nullopt;std::set<int> covered;std::size_t count=0;std::function<bool(std::size_t)> rec=[&](std::size_t i){if(i==subsets.size()){if(covered.size()==universe.size()&&++count>maximum_count)return false;return true;}if(!rec(i+1))return false;bool disjoint=std::none_of(subsets[i].values.begin(),subsets[i].values.end(),[&](int v){return covered.count(v);});if(disjoint){covered.insert(subsets[i].values.begin(),subsets[i].values.end());if(!rec(i+1))return false;for(int v:subsets[i].values)covered.erase(v);}return true;};if(!rec(0))return std::nullopt;return count;""",
        """assert(exact_cover_count({1,2},{{"both",{1,2}},{"one",{1}},{"two",{2}}},3)==2);
    assert(exact_cover_count({}, {}, 1)==1);
    assert(!exact_cover_count({1},{{"a",{1}},{"b",{1}}},0));
    assert(!exact_cover_count({2,1},{},1));
    assert(!exact_cover_count({1},{{"a",{2}}},1));""",
        ["universe and subsets are sorted unique", "subset names are unique and nonempty", "subset values belong to universe", "empty universe has one empty cover", "exceeding maximum count rejects"],
        "include/exclude subset search with disjoint coverage state", ["exact-cover", "counting", "constraint"],
    )
    add(
        "Zebra Puzzle", "redundant-order-clues", "Redundant order clues",
        "Given sorted unique labels and directed before-clues, return clue indices whose removal leaves the same reachability relation. Reject unknown labels, self edges, duplicate edges, or any cycle. Indices are returned ascending.",
        "struct BeforeClue { std::string before; std::string after; };",
        "std::optional<std::vector<std::size_t>> redundant_order_clues(const std::vector<std::string>& labels, const std::vector<BeforeClue>& clues)",
        """if(!std::is_sorted(labels.begin(),labels.end())||std::adjacent_find(labels.begin(),labels.end())!=labels.end()||std::find(labels.begin(),labels.end(),"")!=labels.end())return std::nullopt;std::set<std::pair<int,int>> edges;std::vector<std::pair<int,int>> indexed;for(const auto&c:clues){auto a=std::lower_bound(labels.begin(),labels.end(),c.before),b=std::lower_bound(labels.begin(),labels.end(),c.after);if(a==labels.end()||*a!=c.before||b==labels.end()||*b!=c.after||a==b)return std::nullopt;std::pair<int,int> e{static_cast<int>(a-labels.begin()),static_cast<int>(b-labels.begin())};if(!edges.insert(e).second)return std::nullopt;indexed.push_back(e);}auto closure=[&](std::optional<std::size_t> skip){std::vector<std::vector<bool>> reach(labels.size(),std::vector<bool>(labels.size()));for(std::size_t i=0;i<indexed.size();++i)if(!skip||i!=*skip)reach[indexed[i].first][indexed[i].second]=true;for(std::size_t k=0;k<labels.size();++k)for(std::size_t i=0;i<labels.size();++i)for(std::size_t j=0;j<labels.size();++j)reach[i][j]=reach[i][j]||(reach[i][k]&&reach[k][j]);return reach;};auto full=closure(std::nullopt);for(std::size_t i=0;i<labels.size();++i)if(full[i][i])return std::optional<std::vector<std::size_t>>{};std::vector<std::size_t> out;for(std::size_t i=0;i<clues.size();++i)if(closure(i)==full)out.push_back(i);return out;""",
        """auto r=redundant_order_clues({"a","b","c"},{{"a","b"},{"b","c"},{"a","c"}});assert(r&&*r==(std::vector<std::size_t>{2}));
    assert(redundant_order_clues({},{})->empty());
    assert(!redundant_order_clues({"b","a"},{}));
    assert(!redundant_order_clues({"a"},{{"a","a"}}));
    assert(!redundant_order_clues({"a","b"},{{"a","b"},{"b","a"}}));""",
        ["labels are sorted unique nonempty", "clues are unique known non-self edges", "cyclic clue sets reject", "redundancy preserves complete reachability", "indices refer to original clue order"],
        "transitive-closure equality under single-edge removal", ["clue", "redundancy", "reachability"],
    )
    add(
        "Zebra Puzzle", "latin-house-uniqueness", "Latin house uniqueness",
        "Count solutions to a partial Latin-square house assignment up to a maximum. Zero denotes unknown; each row and column must contain each value one through n once. Reject malformed givens or return no count when the limit is exceeded.",
        "",
        "std::optional<std::size_t> latin_house_solution_count(std::vector<std::vector<int>> grid, std::size_t maximum_count)",
        """const std::size_t n=grid.size();for(const auto&row:grid)if(row.size()!=n)return std::nullopt;for(std::size_t r=0;r<n;++r)for(std::size_t c=0;c<n;++c){int v=grid[r][c];if(v<0||v>static_cast<int>(n))return std::nullopt;if(v){for(std::size_t j=0;j<c;++j)if(grid[r][j]==v)return std::nullopt;for(std::size_t i=0;i<r;++i)if(grid[i][c]==v)return std::nullopt;}}std::size_t count=0;std::function<bool(std::size_t)> rec=[&](std::size_t pos){if(pos==n*n){return ++count<=maximum_count;}std::size_t r=pos/n,c=pos%n;if(grid[r][c])return rec(pos+1);for(int v=1;v<=static_cast<int>(n);++v){bool ok=true;for(std::size_t j=0;j<n;++j)ok=ok&&grid[r][j]!=v;for(std::size_t i=0;i<n;++i)ok=ok&&grid[i][c]!=v;if(ok){grid[r][c]=v;if(!rec(pos+1))return false;grid[r][c]=0;}}return true;};if(!rec(0))return std::nullopt;return count;""",
        """assert(latin_house_solution_count({{1,0},{0,1}},2)==1);
    assert(latin_house_solution_count({},1)==1);
    assert(!latin_house_solution_count({{1,1},{0,0}},2));
    assert(!latin_house_solution_count({{1},{1,0}},2));
    assert(!latin_house_solution_count({{0,0},{0,0}},1));""",
        ["grid is square", "givens range from zero through n", "nonzero givens are row/column consistent", "empty order has one solution", "count above maximum rejects"],
        "row-major Latin-square backtracking with early count cutoff", ["latin-square", "solution-count", "bounded-search"],
    )

    if len(specs) != 51:
        raise ValueError(f"expected 51 independent specifications, got {len(specs)}")
    return specs
