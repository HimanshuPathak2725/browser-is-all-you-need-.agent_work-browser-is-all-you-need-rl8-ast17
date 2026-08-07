#!/usr/bin/env python3
"""Independent clean-room CHARM V1 contract set after rejected v1r/v1s2 plans.

This module contains only owner-authored task specifications.  It deliberately
does not import, rewrite, or derive any earlier proposal or benchmark task.
"""

from __future__ import annotations


def build_specs(Spec):
    specs = []

    def add(topic, slug, title, contract, types, signature, definition, tests, edges, strategy, tags):
        specs.append(Spec(topic, slug, title, contract, types, signature, definition, tests, tuple(edges), strategy, tuple(tags)))

    # Allergies: explicit bit domains, aggregate limits, and schedule filtering.
    add(
        "Allergies", "known-bit-domain-decoder", "Known bit-domain decoder",
        "Decode a score through an explicit allergen-bit domain. Domain entries must have distinct nonzero single-bit values and distinct nonempty names. A score containing any unknown bit is invalid; score zero decodes to an empty list. Return names ordered by ascending bit value.",
        "struct AllergenBit { std::uint32_t bit; std::string name; };",
        "std::optional<std::vector<std::string>> decode_known_allergies(std::uint32_t score, const std::vector<AllergenBit>& domain)",
        """std::optional<std::vector<std::string>> charm::v1n3::allergies::decode_known_allergies(std::uint32_t score, const std::vector<charm::v1n3::allergies::AllergenBit>& domain) {
    std::map<std::uint32_t, std::string> ordered;
    std::set<std::string> names;
    std::uint32_t known = 0;
    for (const auto& entry : domain) {
        if (entry.bit == 0 || (entry.bit & (entry.bit - 1U)) != 0 || entry.name.empty()) return std::nullopt;
        if (!ordered.emplace(entry.bit, entry.name).second || !names.insert(entry.name).second) return std::nullopt;
        known |= entry.bit;
    }
    if ((score & ~known) != 0U) return std::nullopt;
    std::vector<std::string> result;
    for (const auto& entry : ordered) if ((score & entry.first) != 0U) result.push_back(entry.second);
    return result;
}""",
        """using namespace charm::v1n3::allergies;
int main() {
    const std::vector<AllergenBit> domain{{4U,"cats"},{1U,"eggs"},{2U,"nuts"}};
    assert((decode_known_allergies(5U, domain).value()==std::vector<std::string>{"eggs","cats"}));
    assert(decode_known_allergies(0U, domain)->empty());
    assert(!decode_known_allergies(8U, domain));
    assert(!decode_known_allergies(1U, {{3U,"bad"}}));
    assert(!decode_known_allergies(1U, {{1U,"x"},{2U,"x"}}));
    return 0;
}""",
        ("zero score is empty", "unknown score bits reject", "domain bits are powers of two", "domain names and bits are unique", "output follows numeric bit order"),
        "validated bit-domain indexing followed by ordered mask projection", ("bitmask", "domain-validation", "case-sensitive-api"),
    )
    add(
        "Allergies", "exposure-cap-ledger", "Exposure cap ledger",
        "Accumulate named nonnegative exposure units against explicit per-allergen caps. Caps and event names must be nonempty and unique; every event must name a declared cap. Return the allergens whose totals exceed their caps, ordered by descending excess and then name. Invalid input rejects the ledger.",
        "struct ExposureEvent { std::string allergen; int units; };",
        "std::optional<std::vector<std::pair<std::string,int>>> exceeded_exposure_caps(const std::vector<std::pair<std::string,int>>& caps, const std::vector<ExposureEvent>& events)",
        """std::optional<std::vector<std::pair<std::string,int>>> charm::v1n3::allergies::exceeded_exposure_caps(const std::vector<std::pair<std::string,int>>& caps, const std::vector<charm::v1n3::allergies::ExposureEvent>& events) {
    std::map<std::string,int> limit;
    for (const auto& cap : caps) if (cap.first.empty() || cap.second < 0 || !limit.emplace(cap).second) return std::nullopt;
    std::map<std::string,int> totals;
    for (const auto& event : events) {
        if (event.units < 0 || limit.count(event.allergen) == 0) return std::nullopt;
        if (totals[event.allergen] > std::numeric_limits<int>::max() - event.units) return std::nullopt;
        totals[event.allergen] += event.units;
    }
    std::vector<std::pair<std::string,int>> result;
    for (const auto& cap : limit) if (totals[cap.first] > cap.second) result.emplace_back(cap.first, totals[cap.first] - cap.second);
    std::sort(result.begin(), result.end(), [](const auto& a, const auto& b){ return a.second != b.second ? a.second > b.second : a.first < b.first; });
    return result;
}""",
        """using namespace charm::v1n3::allergies;
int main() {
    auto r=exceeded_exposure_caps({{"dust",3},{"pollen",4}},{{"pollen",3},{"dust",5},{"pollen",3}});
    assert(r && *r==(std::vector<std::pair<std::string,int>>{{"dust",2},{"pollen",2}}));
    assert(exceeded_exposure_caps({{"x",0}},{})->empty());
    assert(!exceeded_exposure_caps({{"x",1},{"x",2}},{}));
    assert(!exceeded_exposure_caps({{"x",1}},{{"y",1}}));
    assert(!exceeded_exposure_caps({{"x",1}},{{"x",-1}}));
    return 0;
}""",
        ("negative units reject", "events require declared caps", "duplicate caps reject", "integer overflow rejects", "excess ordering is deterministic"),
        "validated keyed accumulation with overflow checks and excess ranking", ("ledger", "overflow", "ordering"),
    )
    add(
        "Allergies", "meal-mask-filter", "Meal mask filter",
        "Select meal identifiers whose declared allergen masks do not intersect a blocked mask. Meal identifiers must be distinct and nonempty, and every meal mask may use only bits from known_mask. Return selected identifiers in input order; malformed domains reject.",
        "struct MaskedMeal { std::string id; std::uint32_t allergens; };",
        "std::optional<std::vector<std::string>> meals_avoiding_mask(const std::vector<MaskedMeal>& meals, std::uint32_t known_mask, std::uint32_t blocked_mask)",
        """std::optional<std::vector<std::string>> charm::v1n3::allergies::meals_avoiding_mask(const std::vector<charm::v1n3::allergies::MaskedMeal>& meals, std::uint32_t known_mask, std::uint32_t blocked_mask) {
    if ((blocked_mask & ~known_mask) != 0U) return std::nullopt;
    std::set<std::string> ids;
    std::vector<std::string> result;
    for (const auto& meal : meals) {
        if (meal.id.empty() || !ids.insert(meal.id).second || (meal.allergens & ~known_mask) != 0U) return std::nullopt;
        if ((meal.allergens & blocked_mask) == 0U) result.push_back(meal.id);
    }
    return result;
}""",
        """using namespace charm::v1n3::allergies;
int main() {
    assert((meals_avoiding_mask({{"soup",1U},{"rice",0U},{"pie",2U}},3U,1U).value()==std::vector<std::string>{"rice","pie"}));
    assert(meals_avoiding_mask({},0U,0U)->empty());
    assert(!meals_avoiding_mask({{"x",4U}},3U,0U));
    assert(!meals_avoiding_mask({{"x",0U},{"x",0U}},0U,0U));
    assert(!meals_avoiding_mask({},1U,2U));
    return 0;
}""",
        ("blocked bits must be known", "meal bits must be known", "identifiers are unique", "zero masks are supported", "input order is preserved"),
        "domain-mask validation followed by stable conflict filtering", ("bitmask", "filtering", "header-edit"),
    )

    # Bank Account: lifecycle, atomic transfers, and explicitly partitioned aggregation.
    add(
        "Bank Account", "account-lifecycle-machine", "Account lifecycle machine",
        "Replay an account lifecycle beginning closed. open requires a nonnegative opening balance, credit and debit require an open account and positive amounts, debit may not overdraw, and close requires a zero balance. Any invalid transition rejects the entire trace. Return final balance, open flag, and number of completed closures.",
        "enum class AccountAction { open, credit, debit, close }; struct AccountEvent { AccountAction action; long long cents; };",
        "std::optional<std::array<long long,3>> replay_account_lifecycle(const std::vector<AccountEvent>& events)",
        """std::optional<std::array<long long,3>> charm::v1n3::bank_account::replay_account_lifecycle(const std::vector<charm::v1n3::bank_account::AccountEvent>& events) {
    bool open=false; long long balance=0; long long closures=0;
    for (const auto& event : events) {
        if (event.action==AccountAction::open) { if (open || event.cents<0) return std::nullopt; open=true; balance=event.cents; }
        else if (event.action==AccountAction::credit) { if (!open || event.cents<=0 || balance>std::numeric_limits<long long>::max()-event.cents) return std::nullopt; balance+=event.cents; }
        else if (event.action==AccountAction::debit) { if (!open || event.cents<=0 || event.cents>balance) return std::nullopt; balance-=event.cents; }
        else if (event.action==AccountAction::close) { if (!open || event.cents!=0 || balance!=0) return std::nullopt; open=false; ++closures; }
        else return std::nullopt;
    }
    return std::array<long long,3>{balance,open?1LL:0LL,closures};
}""",
        """using namespace charm::v1n3::bank_account;
int main() {
    auto r=replay_account_lifecycle({{AccountAction::open,100},{AccountAction::debit,100},{AccountAction::close,0},{AccountAction::open,5}});
    assert(r && *r==(std::array<long long,3>{5,1,1}));
    assert(replay_account_lifecycle({})->at(1)==0);
    assert(!replay_account_lifecycle({{AccountAction::credit,1}}));
    assert(!replay_account_lifecycle({{AccountAction::open,1},{AccountAction::close,0}}));
    assert(!replay_account_lifecycle({{AccountAction::open,-1}}));
    return 0;
}""",
        ("opening twice rejects", "money actions require open state", "overdraft rejects", "close requires zero", "overflow rejects"),
        "explicit finite-state replay with checked monetary transitions", ("lifecycle", "state-machine", "api-repair"),
    )
    add(
        "Bank Account", "atomic-transfer-batch", "Atomic transfer batch",
        "Apply a batch of positive transfers to a unique-name balance table. Every endpoint must exist and differ, no transfer may overdraw, and arithmetic overflow rejects. The operation is atomic: return no result on any failure; otherwise return balances in lexical account order.",
        "struct Transfer { std::string from; std::string to; long long cents; };",
        "std::optional<std::vector<std::pair<std::string,long long>>> settle_transfer_batch(const std::vector<std::pair<std::string,long long>>& balances, const std::vector<Transfer>& transfers)",
        """std::optional<std::vector<std::pair<std::string,long long>>> charm::v1n3::bank_account::settle_transfer_batch(const std::vector<std::pair<std::string,long long>>& balances, const std::vector<charm::v1n3::bank_account::Transfer>& transfers) {
    std::map<std::string,long long> state;
    for (const auto& item : balances) if (item.first.empty() || item.second<0 || !state.emplace(item).second) return std::nullopt;
    for (const auto& transfer : transfers) {
        auto from=state.find(transfer.from), to=state.find(transfer.to);
        if (transfer.cents<=0 || from==state.end() || to==state.end() || from==to || from->second<transfer.cents) return std::nullopt;
        if (to->second>std::numeric_limits<long long>::max()-transfer.cents) return std::nullopt;
        from->second-=transfer.cents; to->second+=transfer.cents;
    }
    return std::vector<std::pair<std::string,long long>>(state.begin(),state.end());
}""",
        """using namespace charm::v1n3::bank_account;
int main() {
    auto r=settle_transfer_batch({{"b",5},{"a",10}},{{"a","b",4},{"b","a",2}});
    assert(r && *r==(std::vector<std::pair<std::string,long long>>{{"a",8},{"b",7}}));
    assert(settle_transfer_batch({},{})->empty());
    assert(!settle_transfer_batch({{"a",1},{"a",2}},{}));
    assert(!settle_transfer_batch({{"a",1},{"b",0}},{{"a","b",2}}));
    assert(!settle_transfer_batch({{"a",1}},{{"a","a",1}}));
    return 0;
}""",
        ("accounts are unique", "amounts are positive", "self-transfer rejects", "batch failure is atomic", "output order is lexical"),
        "copy-on-validate ledger replay with checked endpoints and balances", ("atomicity", "transfer", "linker-repair"),
    )
    add(
        "Bank Account", "partitioned-posting-sum", "Partitioned posting sum",
        "Sum signed postings using exactly min(worker_count, posting_count) asynchronous partitions. worker_count zero is invalid even for empty input. Detect signed overflow both within partitions and during the deterministic left-to-right reduction.",
        "",
        "std::optional<long long> partitioned_posting_sum(const std::vector<long long>& postings, std::size_t worker_count)",
        """std::optional<long long> charm::v1n3::bank_account::partitioned_posting_sum(const std::vector<long long>& postings, std::size_t worker_count) {
    if (worker_count==0) return std::nullopt;
    if (postings.empty()) return 0LL;
    const std::size_t workers=std::min(worker_count,postings.size());
    std::vector<std::future<std::optional<long long>>> jobs;
    for (std::size_t w=0;w<workers;++w) jobs.push_back(std::async(std::launch::async,[&,w]{ long long sum=0; for(std::size_t i=w;i<postings.size();i+=workers){long long x=postings[i]; if((x>0&&sum>std::numeric_limits<long long>::max()-x)||(x<0&&sum<std::numeric_limits<long long>::min()-x))return std::optional<long long>{}; sum+=x;} return std::optional<long long>{sum}; }));
    long long total=0;
    for(auto& job:jobs){auto part=job.get();if(!part)return std::nullopt;long long x=*part;if((x>0&&total>std::numeric_limits<long long>::max()-x)||(x<0&&total<std::numeric_limits<long long>::min()-x))return std::nullopt;total+=x;}
    return total;
}""",
        """using charm::v1n3::bank_account::partitioned_posting_sum;
int main() {
    assert(partitioned_posting_sum({5,-2,7,-1},3)==9);
    assert(partitioned_posting_sum({},2)==0);
    assert(!partitioned_posting_sum({},0));
    assert(partitioned_posting_sum({1,2},9)==3);
    assert(!partitioned_posting_sum({std::numeric_limits<long long>::max(),1},1));
    return 0;
}""",
        ("zero workers reject", "empty postings sum to zero with workers", "workers are capped", "signed overflow rejects", "reduction order is deterministic"),
        "strided asynchronous partitions with optional checked reductions", ("thread-safe", "async", "overflow"),
    )

    # Binary Search Tree: unique ownership, link validation, and rank invariants.
    add(
        "Binary Search Tree", "owned-duplicate-policy-build", "Owned duplicate-policy build",
        "Build a non-templated integer search tree using unique ownership. The explicit duplicate policy chooses whether equal keys descend left, descend right, or reject the input. Return the inorder traversal and maximum root depth; empty input has depth -1.",
        "enum class DuplicatePolicy { reject, left, right }; struct TreeBuildSummary { std::vector<int> inorder; int max_depth; };",
        "std::optional<TreeBuildSummary> build_owned_tree(const std::vector<int>& keys, DuplicatePolicy policy)",
        """std::optional<charm::v1n3::binary_search_tree::TreeBuildSummary> charm::v1n3::binary_search_tree::build_owned_tree(const std::vector<int>& keys, charm::v1n3::binary_search_tree::DuplicatePolicy policy) {
    struct Node { int value; std::unique_ptr<Node> left; std::unique_ptr<Node> right; explicit Node(int v):value(v){} };
    std::unique_ptr<Node> root;
    for(int key:keys){std::unique_ptr<Node>* link=&root;while(*link){if(key<(*link)->value)link=&(*link)->left;else if(key>(*link)->value)link=&(*link)->right;else if(policy==DuplicatePolicy::left)link=&(*link)->left;else if(policy==DuplicatePolicy::right)link=&(*link)->right;else return std::nullopt;}*link=std::make_unique<Node>(key);}
    TreeBuildSummary result{{},-1};std::function<void(const Node*,int)>visit=[&](const Node* n,int depth){if(!n)return;visit(n->left.get(),depth+1);result.inorder.push_back(n->value);result.max_depth=std::max(result.max_depth,depth);visit(n->right.get(),depth+1);};visit(root.get(),0);return result;
}""",
        """using namespace charm::v1n3::binary_search_tree;
int main() {
    auto r=build_owned_tree({4,2,6,2},DuplicatePolicy::right);assert(r&&r->inorder==(std::vector<int>{2,2,4,6})&&r->max_depth==2);
    assert(build_owned_tree({},DuplicatePolicy::reject)->max_depth==-1);
    assert(!build_owned_tree({1,1},DuplicatePolicy::reject));
    assert(build_owned_tree({1,1},DuplicatePolicy::left)->max_depth==1);
    assert(build_owned_tree({3,1,5},DuplicatePolicy::reject)->max_depth==1);
    return 0;
}""",
        ("ownership is unique", "duplicate behavior is explicit", "empty depth is minus one", "inorder preserves multiplicity", "depth starts at zero"),
        "iterative owned-link insertion plus recursive invariant projection", ("unique-ptr", "duplicate-policy", "traversal"),
    )
    add(
        "Binary Search Tree", "indexed-tree-level-widths", "Indexed tree level widths",
        "Validate an indexed binary-tree description rooted at node zero and return the width of every level. Child indices use -1 for absence. Reject out-of-range children, repeated parents, cycles, unreachable nodes, and duplicate keys when strict ordering is required.",
        "struct IndexedTreeNode { int key; int left; int right; };",
        "std::optional<std::vector<std::size_t>> strict_tree_level_widths(const std::vector<IndexedTreeNode>& nodes)",
        """std::optional<std::vector<std::size_t>> charm::v1n3::binary_search_tree::strict_tree_level_widths(const std::vector<charm::v1n3::binary_search_tree::IndexedTreeNode>& nodes) {
    if (nodes.empty()) return std::vector<std::size_t>{};
    std::vector<int> parents(nodes.size(),0);for(const auto& n:nodes)for(int c:{n.left,n.right}){if(c<-1||c>=static_cast<int>(nodes.size()))return std::nullopt;if(c>=0&&++parents[static_cast<std::size_t>(c)]>1)return std::nullopt;}if(parents[0]!=0)return std::nullopt;
    std::vector<bool> seen(nodes.size());std::queue<std::tuple<int,long long,long long,std::size_t>> q;q.emplace(0,std::numeric_limits<long long>::min(),std::numeric_limits<long long>::max(),0);std::vector<std::size_t> widths;
    while(!q.empty()){auto [i,low,high,depth]=q.front();q.pop();if(seen[static_cast<std::size_t>(i)])return std::nullopt;seen[static_cast<std::size_t>(i)]=true;long long key=nodes[static_cast<std::size_t>(i)].key;if(key<=low||key>=high)return std::nullopt;if(widths.size()==depth)widths.push_back(0);++widths[depth];auto n=nodes[static_cast<std::size_t>(i)];if(n.left>=0)q.emplace(n.left,low,key,depth+1);if(n.right>=0)q.emplace(n.right,key,high,depth+1);}
    if (std::find(seen.begin(),seen.end(),false)!=seen.end()) return std::nullopt;
    return widths;
}""",
        """using namespace charm::v1n3::binary_search_tree;
int main() {
    assert((strict_tree_level_widths({{4,1,2},{2,-1,-1},{6,-1,-1}}).value()==std::vector<std::size_t>{1,2}));
    assert(strict_tree_level_widths({})->empty());
    assert(!strict_tree_level_widths({{1,0,-1}}));
    assert(!strict_tree_level_widths({{2,1,-1},{3,-1,-1}}));
    assert(!strict_tree_level_widths({{1,-1,-1},{2,-1,-1}}));
    return 0;
}""",
        ("root is index zero", "minus one denotes no child", "every node is reachable once", "keys are strictly ordered", "empty description is valid"),
        "parent-count validation followed by bounded breadth-first ordering proof", ("index-graph", "breadth-first", "header-placement"),
    )
    add(
        "Binary Search Tree", "rank-interval-counts", "Rank interval counts",
        "Given insertion keys with duplicates rejected, answer half-open rank intervals [first,last) over the sorted tree contents. Return sums for valid intervals and reject the complete request if any bound is reversed or exceeds the node count.",
        "struct RankInterval { std::size_t first; std::size_t last; };",
        "std::optional<std::vector<long long>> tree_rank_interval_sums(const std::vector<int>& insertion_keys, const std::vector<RankInterval>& intervals)",
        """std::optional<std::vector<long long>> charm::v1n3::binary_search_tree::tree_rank_interval_sums(const std::vector<int>& insertion_keys, const std::vector<charm::v1n3::binary_search_tree::RankInterval>& intervals) {
    std::set<int> unique(insertion_keys.begin(),insertion_keys.end());if(unique.size()!=insertion_keys.size())return std::nullopt;std::vector<long long> prefix(1,0);for(int key:unique)prefix.push_back(prefix.back()+key);std::vector<long long> result;for(const auto& interval:intervals){if(interval.first>interval.last||interval.last>unique.size())return std::nullopt;result.push_back(prefix[interval.last]-prefix[interval.first]);}return result;
}""",
        """using namespace charm::v1n3::binary_search_tree;
int main() {
    assert((tree_rank_interval_sums({5,1,3},{{0,2},{1,3},{2,2}}).value()==std::vector<long long>{4,8,0}));
    assert(tree_rank_interval_sums({},{})->empty());
    assert(!tree_rank_interval_sums({1,1},{}));
    assert(!tree_rank_interval_sums({1},{{0,2}}));
    assert(tree_rank_interval_sums({-2,4},{{0,2}})->at(0)==2);
    return 0;
}""",
        ("duplicates reject", "intervals are half-open", "empty intervals sum to zero", "invalid bounds reject all", "negative keys are supported"),
        "ordered-set rank projection with prefix-sum interval evaluation", ("rank", "prefix-sum", "invariant"),
    )

    # Circular Buffer: nontrivial values, transaction rollback, and logical rotation.
    add(
        "Circular Buffer", "string-ring-lifetime-replay", "String ring lifetime replay",
        "Replay push, pop, and clear operations on a fixed-capacity ring of std::string values. Push on full either overwrites the oldest value or rejects according to the explicit mode; pop on empty rejects. Capacity zero is valid only for traces containing clear operations. Return the final logical order and pop history.",
        "enum class RingOpKind { push, pop, clear }; struct RingOp { RingOpKind kind; std::string value; }; struct RingReplay { std::vector<std::string> remaining; std::vector<std::string> popped; };",
        "std::optional<RingReplay> replay_string_ring(std::size_t capacity, bool overwrite, const std::vector<RingOp>& operations)",
        """std::optional<charm::v1n3::circular_buffer::RingReplay> charm::v1n3::circular_buffer::replay_string_ring(std::size_t capacity, bool overwrite, const std::vector<charm::v1n3::circular_buffer::RingOp>& operations) {
    std::deque<std::string> ring;RingReplay result;
    for(const auto& op:operations){if(op.kind==RingOpKind::push){if(capacity==0)return std::nullopt;if(ring.size()==capacity){if(!overwrite)return std::nullopt;ring.pop_front();}ring.push_back(op.value);}else if(op.kind==RingOpKind::pop){if(!op.value.empty()||ring.empty())return std::nullopt;result.popped.push_back(std::move(ring.front()));ring.pop_front();}else if(op.kind==RingOpKind::clear){if(!op.value.empty())return std::nullopt;ring.clear();}else return std::nullopt;}
    result.remaining.assign(ring.begin(),ring.end());return result;
}""",
        """using namespace charm::v1n3::circular_buffer;
int main() {
    auto r=replay_string_ring(2,true,{{RingOpKind::push,"a"},{RingOpKind::push,"b"},{RingOpKind::push,"c"},{RingOpKind::pop,""}});assert(r&&r->popped==std::vector<std::string>{"b"}&&r->remaining==std::vector<std::string>{"c"});
    assert(replay_string_ring(0,false,{{RingOpKind::clear,""}})->remaining.empty());
    assert(!replay_string_ring(0,true,{{RingOpKind::push,"x"}}));
    assert(!replay_string_ring(1,false,{{RingOpKind::pop,""}}));
    assert(!replay_string_ring(1,false,{{RingOpKind::push,"x"},{RingOpKind::push,"y"}}));
    return 0;
}""",
        ("strings exercise nontrivial lifetime", "overwrite removes oldest", "pop history is ordered", "zero capacity is explicit", "operation payloads are validated"),
        "deque-backed logical ring replay with move-aware removal", ("nontrivial-lifetime", "overwrite", "asan"),
    )
    add(
        "Circular Buffer", "transactional-ring-batches", "Transactional ring batches",
        "Apply batches of integer pushes to a bounded ring. Each batch is atomic: if reject_on_full is true and the complete batch cannot fit, leave the ring unchanged and mark that batch rejected; otherwise overwrite oldest elements as needed. Return the final ring and one acceptance flag per batch.",
        "struct RingBatchResult { std::vector<int> values; std::vector<bool> accepted; };",
        "std::optional<RingBatchResult> apply_ring_batches(std::size_t capacity, bool reject_on_full, const std::vector<std::vector<int>>& batches)",
        """std::optional<charm::v1n3::circular_buffer::RingBatchResult> charm::v1n3::circular_buffer::apply_ring_batches(std::size_t capacity, bool reject_on_full, const std::vector<std::vector<int>>& batches) {
    if(capacity==0){for(const auto& b:batches)if(!b.empty())return std::nullopt;}std::deque<int> ring;RingBatchResult result;
    for(const auto& batch:batches){if(reject_on_full&&batch.size()>capacity-ring.size()){result.accepted.push_back(false);continue;}for(int value:batch){if(ring.size()==capacity)ring.pop_front();ring.push_back(value);}result.accepted.push_back(true);}result.values.assign(ring.begin(),ring.end());return result;
}""",
        """using namespace charm::v1n3::circular_buffer;
int main() {
    auto r=apply_ring_batches(3,true,{{1,2},{3,4},{5}});assert(r&&r->values==(std::vector<int>{1,2,5})&&r->accepted==(std::vector<bool>{true,false,true}));
    auto o=apply_ring_batches(2,false,{{1,2,3}});assert(o&&o->values==(std::vector<int>{2,3}));
    assert(apply_ring_batches(0,true,{{}})->accepted==std::vector<bool>{true});
    assert(!apply_ring_batches(0,false,{{1}}));
    assert(apply_ring_batches(2,true,{})->values.empty());
    return 0;
}""",
        ("batch rejection rolls back", "overwrite mode accepts long batches", "zero capacity rejects values", "empty batches are accepted", "flags align with batches"),
        "capacity precheck for rollback mode plus bounded overwrite commits", ("exception-safety", "transaction", "rollback"),
    )
    add(
        "Circular Buffer", "logical-ring-rotation", "Logical ring rotation",
        "Rotate a logical ring snapshot by a signed offset without changing capacity. Positive offsets move the front toward the back, negative offsets move the back toward the front, and offsets normalize modulo size. Empty snapshots always remain empty.",
        "",
        "std::vector<int> rotate_ring_snapshot(std::vector<int> values, long long offset)",
        """std::vector<int> charm::v1n3::circular_buffer::rotate_ring_snapshot(std::vector<int> values, long long offset) {
    if (values.empty()) return values;
    long long n=static_cast<long long>(values.size());long long shift=offset%n;if(shift<0)shift+=n;std::rotate(values.begin(),values.begin()+shift,values.end());return values;
}""",
        """using charm::v1n3::circular_buffer::rotate_ring_snapshot;
int main() {
    assert((rotate_ring_snapshot({1,2,3,4},1)==std::vector<int>{2,3,4,1}));
    assert((rotate_ring_snapshot({1,2,3,4},-1)==std::vector<int>{4,1,2,3}));
    assert(rotate_ring_snapshot({},99).empty());
    assert((rotate_ring_snapshot({7},-100)==std::vector<int>{7}));
    assert((rotate_ring_snapshot({1,2},4)==std::vector<int>{1,2}));
    return 0;
}""",
        ("signed offsets normalize", "empty input avoids modulo", "positive moves front to back", "negative moves back to front", "multiples preserve order"),
        "normalized signed modular rotation over constructed elements", ("rotation", "normalization", "lifetime"),
    )

    # Clock: exact public type/factory/operators plus offset and overlap arithmetic.
    add(
        "Clock", "exact-clock-factory", "Exact clock factory",
        "Provide the exact case-sensitive ExactClock type and make_exact_clock factory. The factory accepts arbitrary signed hours and minutes and normalizes to a 24-hour day. ExactClock exposes minutes_since_midnight, equality, and signed minute addition with wraparound.",
        "class ExactClock { public: explicit ExactClock(int minute); int minutes_since_midnight() const; ExactClock operator+(long long delta) const; bool operator==(const ExactClock& other) const; private: int minute_; };",
        "ExactClock make_exact_clock(long long hours, long long minutes)",
        """charm::v1n3::clock::ExactClock charm::v1n3::clock::make_exact_clock(long long hours, long long minutes) { long long value=(hours%24LL)*60LL+(minutes%1440LL);value%=1440LL;if(value<0)value+=1440LL;return ExactClock(static_cast<int>(value)); }
charm::v1n3::clock::ExactClock::ExactClock(int minute):minute_(minute){}
int charm::v1n3::clock::ExactClock::minutes_since_midnight() const{return minute_;}
charm::v1n3::clock::ExactClock charm::v1n3::clock::ExactClock::operator+(long long delta) const{return make_exact_clock(0,static_cast<long long>(minute_)+(delta%1440LL));}
bool charm::v1n3::clock::ExactClock::operator==(const ExactClock& other) const{return minute_==other.minute_;}""",
        """using namespace charm::v1n3::clock;
int main() {
    assert(make_exact_clock(25,-1).minutes_since_midnight()==1499%1440);
    assert(make_exact_clock(-1,0).minutes_since_midnight()==1380);
    assert((make_exact_clock(23,59)+2)==make_exact_clock(0,1));
    assert((make_exact_clock(0,0)+(-1))==make_exact_clock(23,59));
    assert(make_exact_clock(48,0)==make_exact_clock(0,0));
    return 0;
}""",
        ("API spelling is exact", "hours and minutes are signed", "normalization is modulo one day", "addition wraps both ways", "equality compares normalized time"),
        "wide signed normalization behind a value type and exact operators", ("case-sensitive-api", "factory", "operator"),
    )
    add(
        "Clock", "offset-segment-conversion", "Offset segment conversion",
        "Convert local minute readings through a schedule of UTC offsets. Each segment begins at a nonnegative local minute and segments must be strictly increasing; the first segment begins at zero. Return normalized UTC minutes in [0,1439] while preserving input order.",
        "struct OffsetSegment { int local_begin; int offset_minutes; };",
        "std::optional<std::vector<int>> local_readings_to_utc(const std::vector<int>& local_minutes, const std::vector<OffsetSegment>& segments)",
        """std::optional<std::vector<int>> charm::v1n3::clock::local_readings_to_utc(const std::vector<int>& local_minutes, const std::vector<charm::v1n3::clock::OffsetSegment>& segments) {
    if (segments.empty()||segments.front().local_begin!=0) return std::nullopt;
    for (std::size_t i=1;i<segments.size();++i) {
        if (segments[i].local_begin<=segments[i-1].local_begin) return std::nullopt;
    }
    std::vector<int> result;
    for(int local:local_minutes){if(local<0)return std::nullopt;auto it=std::upper_bound(segments.begin(),segments.end(),local,[](int value,const OffsetSegment& s){return value<s.local_begin;});--it;long long utc=static_cast<long long>(local)-it->offset_minutes;utc%=1440;if(utc<0)utc+=1440;result.push_back(static_cast<int>(utc));}return result;
}""",
        """using namespace charm::v1n3::clock;
int main() {
    assert((local_readings_to_utc({0,90,150},{{0,60},{120,120}}).value()==std::vector<int>{1380,30,30}));
    assert(!local_readings_to_utc({},{}));
    assert(!local_readings_to_utc({},{{1,0}}));
    assert(!local_readings_to_utc({-1},{{0,0}}));
    assert(!local_readings_to_utc({},{{0,0},{0,1}}));
    return 0;
}""",
        ("schedule starts at zero", "segment starts increase", "readings are nonnegative", "UTC wraps by one day", "input order is stable"),
        "upper-bound segment lookup with signed modular conversion", ("offset", "schedule", "wraparound"),
    )
    add(
        "Clock", "cyclic-interval-overlap", "Cyclic interval overlap",
        "Count overlapping minutes between two half-open daily intervals. Each interval is described by a normalized start minute and a duration from 0 through 1440; intervals may cross midnight. Invalid starts or durations reject.",
        "struct DailyInterval { int start_minute; int duration; };",
        "std::optional<int> cyclic_overlap_minutes(DailyInterval first, DailyInterval second)",
        """std::optional<int> charm::v1n3::clock::cyclic_overlap_minutes(charm::v1n3::clock::DailyInterval first, charm::v1n3::clock::DailyInterval second) {
    auto valid=[](DailyInterval x){return x.start_minute>=0&&x.start_minute<1440&&x.duration>=0&&x.duration<=1440;};if(!valid(first)||!valid(second))return std::nullopt;int total=0;for(int minute=0;minute<1440;++minute){auto inside=[&](DailyInterval x){int delta=(minute-x.start_minute+1440)%1440;return delta<x.duration;};if(inside(first)&&inside(second))++total;}return total;
}""",
        """using namespace charm::v1n3::clock;
int main() {
    assert(cyclic_overlap_minutes({1380,120},{0,90})==60);
    assert(cyclic_overlap_minutes({0,0},{0,1440})==0);
    assert(cyclic_overlap_minutes({0,1440},{500,1440})==1440);
    assert(!cyclic_overlap_minutes({-1,1},{0,1}));
    assert(!cyclic_overlap_minutes({0,1441},{0,1}));
    return 0;
}""",
        ("intervals are half-open", "midnight crossing is cyclic", "zero duration is empty", "duration 1440 is full day", "starts are normalized inputs"),
        "bounded minute-domain membership intersection", ("cyclic", "interval", "boundary"),
    )

    # Complex Numbers: encapsulated value access, polynomial evaluation, safe division.
    add(
        "Complex Numbers", "encapsulated-complex-value", "Encapsulated complex value",
        "Construct an EncapsulatedComplex through make_encapsulated_complex. Its representation remains private; public real, imag, magnitude_squared, conjugate, and equality operations define all observable behavior.",
        "class EncapsulatedComplex { public: EncapsulatedComplex(double real, double imag); double real() const; double imag() const; double magnitude_squared() const; EncapsulatedComplex conjugate() const; bool operator==(const EncapsulatedComplex& other) const; private: double real_; double imag_; };",
        "EncapsulatedComplex make_encapsulated_complex(double real, double imag)",
        """charm::v1n3::complex_numbers::EncapsulatedComplex charm::v1n3::complex_numbers::make_encapsulated_complex(double real,double imag){return EncapsulatedComplex(real,imag);}
charm::v1n3::complex_numbers::EncapsulatedComplex::EncapsulatedComplex(double real,double imag):real_(real),imag_(imag){}
double charm::v1n3::complex_numbers::EncapsulatedComplex::real() const{return real_;}
double charm::v1n3::complex_numbers::EncapsulatedComplex::imag() const{return imag_;}
double charm::v1n3::complex_numbers::EncapsulatedComplex::magnitude_squared() const{return real_*real_+imag_*imag_;}
charm::v1n3::complex_numbers::EncapsulatedComplex charm::v1n3::complex_numbers::EncapsulatedComplex::conjugate() const{return EncapsulatedComplex(real_,-imag_);}
bool charm::v1n3::complex_numbers::EncapsulatedComplex::operator==(const EncapsulatedComplex& other) const{return real_==other.real_&&imag_==other.imag_;}""",
        """using namespace charm::v1n3::complex_numbers;
int main() {
    auto z=make_encapsulated_complex(3.0,4.0);assert(z.real()==3.0&&z.imag()==4.0&&z.magnitude_squared()==25.0);
    assert(z.conjugate()==make_encapsulated_complex(3.0,-4.0));
    assert(make_encapsulated_complex(0.0,0.0).magnitude_squared()==0.0);
    assert(!(z==make_encapsulated_complex(3.0,5.0)));
    assert(make_encapsulated_complex(-2.0,1.5).conjugate()==make_encapsulated_complex(-2.0,-1.5));
    return 0;
}""",
        ("representation is private", "accessors are const", "conjugation flips only imaginary sign", "magnitude is squared without a root", "equality is exact"),
        "encapsulated two-scalar value semantics through public accessors", ("encapsulation", "accessor", "strict-compile"),
    )
    add(
        "Complex Numbers", "horner-complex-polynomial", "Horner complex polynomial",
        "Evaluate a complex polynomial whose coefficients are ordered from highest degree through constant using Horner's method. Empty coefficients denote the zero polynomial. Reject any non-finite coefficient or input component.",
        "",
        "std::optional<std::complex<double>> evaluate_complex_polynomial(const std::vector<std::complex<double>>& coefficients, std::complex<double> point)",
        """std::optional<std::complex<double>> charm::v1n3::complex_numbers::evaluate_complex_polynomial(const std::vector<std::complex<double>>& coefficients,std::complex<double> point){auto finite=[](std::complex<double> z){return std::isfinite(z.real())&&std::isfinite(z.imag());};if(!finite(point)||std::any_of(coefficients.begin(),coefficients.end(),[&](auto z){return !finite(z);}))return std::nullopt;std::complex<double> value{0.0,0.0};for(auto coefficient:coefficients)value=value*point+coefficient;if(!finite(value))return std::nullopt;return value;}""",
        """using charm::v1n3::complex_numbers::evaluate_complex_polynomial;
int main() {
    using C=std::complex<double>;assert((evaluate_complex_polynomial({C{1,0},C{0,0},C{-1,0}},C{2,0})==C{3,0}));
    assert((evaluate_complex_polynomial({},C{9,2})==C{0,0}));
    assert((evaluate_complex_polynomial({C{0,1}},C{2,3})==C{0,1}));
    assert(!evaluate_complex_polynomial({C{std::numeric_limits<double>::infinity(),0}},C{0,0}));
    assert(!evaluate_complex_polynomial({},C{std::numeric_limits<double>::quiet_NaN(),0}));
    return 0;
}""",
        ("coefficient order is explicit", "empty polynomial is zero", "non-finite inputs reject", "non-finite result rejects", "Horner order is deterministic"),
        "finite-guarded Horner recurrence over standard complex values", ("polynomial", "precision", "horner"),
    )
    add(
        "Complex Numbers", "scaled-safe-division", "Scaled safe division",
        "Divide two complex values using a scale-aware real arithmetic formula. A denominator whose magnitude is at most epsilon rejects, as do negative epsilon and non-finite components. Return a finite quotient only.",
        "",
        "std::optional<std::complex<double>> divide_complex_scaled(std::complex<double> numerator, std::complex<double> denominator, double epsilon)",
        """std::optional<std::complex<double>> charm::v1n3::complex_numbers::divide_complex_scaled(std::complex<double> numerator,std::complex<double> denominator,double epsilon){auto finite=[](std::complex<double> z){return std::isfinite(z.real())&&std::isfinite(z.imag());};if(epsilon<0||!std::isfinite(epsilon)||!finite(numerator)||!finite(denominator)||std::abs(denominator)<=epsilon)return std::nullopt;auto value=numerator/denominator;if(!finite(value))return std::nullopt;return value;}""",
        """using charm::v1n3::complex_numbers::divide_complex_scaled;
int main() {
    using C=std::complex<double>;auto r=divide_complex_scaled(C{3,1},C{1,-1},0.0);assert(r&&std::abs(*r-C{1,2})<1e-12);
    assert(!divide_complex_scaled(C{1,0},C{0,0},0.0));
    assert(!divide_complex_scaled(C{1,0},C{1,0},-1.0));
    assert((divide_complex_scaled(C{0,0},C{2,0},0.0)==C{0,0}));
    assert(!divide_complex_scaled(C{1,0},C{0.001,0},0.01));
    return 0;
}""",
        ("epsilon is nonnegative", "near-zero denominator rejects", "all components are finite", "zero numerator is valid", "result must remain finite"),
        "public standard-complex operations with scale threshold and finiteness proof", ("division", "epsilon", "public-api"),
    )

    # Crypto Square: explicit topology, bounded formatting, and authenticated decoding.
    add(
        "Crypto Square", "keyed-column-transposition", "Keyed column transposition",
        "Normalize ASCII alphanumeric input to lowercase, place it row-major into exactly key.size columns, pad the final row with the declared non-alphanumeric pad byte, then emit columns in stable key-character order with original key position as the tie break. The public topology is this free function; empty or non-alphanumeric keys reject.",
        "", "std::optional<std::string> keyed_column_encode(std::string_view text, std::string_view key, char pad)",
        """std::optional<std::string> charm::v1n3::crypto_square::keyed_column_encode(std::string_view text,std::string_view key,char pad){if(key.empty()||std::isalnum(static_cast<unsigned char>(pad)))return std::nullopt;for(char c:key)if(!std::isalnum(static_cast<unsigned char>(c)))return std::nullopt;std::string clean;for(char c:text)if(std::isalnum(static_cast<unsigned char>(c)))clean.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(c))));std::size_t rows=(clean.size()+key.size()-1)/key.size();clean.resize(rows*key.size(),pad);std::vector<std::size_t> order(key.size());std::iota(order.begin(),order.end(),0);std::stable_sort(order.begin(),order.end(),[&](auto a,auto b){char x=static_cast<char>(std::tolower(static_cast<unsigned char>(key[a]))),y=static_cast<char>(std::tolower(static_cast<unsigned char>(key[b])));return x<y;});std::string out;for(std::size_t col:order)for(std::size_t row=0;row<rows;++row)out.push_back(clean[row*key.size()+col]);return out;}""",
        """using charm::v1n3::crypto_square::keyed_column_encode;
int main(){assert(keyed_column_encode("A b-c!","ba",'_')=="b_ac");assert(keyed_column_encode("", "x", '_')=="");assert(!keyed_column_encode("x","",'_'));assert(!keyed_column_encode("x","a-",'_'));assert(!keyed_column_encode("x","a",'7'));return 0;}""",
        ("topology is one free function", "all text bytes are normalized or ignored", "key order is stable", "pad participates in output", "output length is bounded by one padded row"),
        "stable keyed-column permutation over a bounded normalized rectangle", ("free-function", "formatting", "warning-clean"),
    )
    add(
        "Crypto Square", "length-framed-blocks", "Length-framed blocks",
        "Normalize ASCII letters to uppercase and digits unchanged, split into blocks of exactly width except the last, and prefix every block with its decimal payload length followed by a colon. width must be from 1 through 99. Join frames with the supplied separator, which must be non-alphanumeric.",
        "", "std::optional<std::string> frame_normalized_blocks(std::string_view text, std::size_t width, char separator)",
        """std::optional<std::string> charm::v1n3::crypto_square::frame_normalized_blocks(std::string_view text,std::size_t width,char separator){if(width==0||width>99||std::isalnum(static_cast<unsigned char>(separator)))return std::nullopt;std::string clean;for(char c:text)if(std::isalnum(static_cast<unsigned char>(c)))clean.push_back(static_cast<char>(std::toupper(static_cast<unsigned char>(c))));std::string out;for(std::size_t i=0;i<clean.size();i+=width){if(!out.empty())out.push_back(separator);std::size_t count=std::min(width,clean.size()-i);out+=std::to_string(count);out.push_back(':');out.append(clean,i,count);}return out;}""",
        """using charm::v1n3::crypto_square::frame_normalized_blocks;
int main(){assert(frame_normalized_blocks("ab-cd9",2,'|')=="2:AB|2:CD|1:9");assert(frame_normalized_blocks("!!!",3,'_')=="");assert(!frame_normalized_blocks("a",0,'_'));assert(!frame_normalized_blocks("a",100,'_'));assert(!frame_normalized_blocks("a",1,'x'));return 0;}""",
        ("width is fully used", "separator is fully used", "empty normalized text emits empty", "frame length is explicit", "no trailing separator"),
        "bounded normalization followed by self-delimiting block emission", ("framing", "input-use", "termination-budget"),
    )
    add(
        "Crypto Square", "checksum-grid-decoder", "Checksum grid decoder",
        "Decode a rectangular row-major payload whose final byte is a lowercase hexadecimal checksum equal to the sum of preceding unsigned bytes modulo 16. rows and columns describe the payload before the checksum and both must be nonzero. Return column-major payload on a valid frame.",
        "", "std::optional<std::string> decode_checked_grid(std::string_view frame, std::size_t rows, std::size_t columns)",
        """std::optional<std::string> charm::v1n3::crypto_square::decode_checked_grid(std::string_view frame,std::size_t rows,std::size_t columns){if(rows==0||columns==0||rows>std::numeric_limits<std::size_t>::max()/columns)return std::nullopt;std::size_t count=rows*columns;if(frame.size()!=count+1)return std::nullopt;unsigned sum=0;for(std::size_t i=0;i<count;++i)sum+=static_cast<unsigned char>(frame[i]);char expected="0123456789abcdef"[sum%16U];if(frame[count]!=expected)return std::nullopt;std::string out;out.reserve(count);for(std::size_t c=0;c<columns;++c)for(std::size_t r=0;r<rows;++r)out.push_back(frame[r*columns+c]);return out;}""",
        """using charm::v1n3::crypto_square::decode_checked_grid;
int main(){assert(decode_checked_grid("abcda",2,2)=="acbd");assert(!decode_checked_grid("abcdb",2,2));assert(!decode_checked_grid("x0",0,1));assert(!decode_checked_grid("x0",1,0));assert(!decode_checked_grid("ab0",1,1));return 0;}""",
        ("shape is exact", "checksum byte is lowercase hex", "checksum uses unsigned bytes", "column-major order is explicit", "dimension multiplication is checked"),
        "shape validation and checksum authentication before transposed decoding", ("decoder", "checksum", "shape"),
    )

    # Diamond: deterministic rectangular renderings and independent symmetry validation.
    add(
        "Diamond", "rectangular-outline-diamond", "Rectangular outline diamond",
        "Render an outline diamond of nonnegative radius as exactly 2*radius+1 strings, each of the same width. The two boundary positions on each row use ink and every other position uses fill. radius must not exceed 1000 and ink must differ from fill.",
        "", "std::optional<std::vector<std::string>> render_outline_diamond(int radius, char ink, char fill)",
        """std::optional<std::vector<std::string>> charm::v1n3::diamond::render_outline_diamond(int radius,char ink,char fill){if(radius<0||radius>1000||ink==fill)return std::nullopt;int width=2*radius+1;std::vector<std::string> rows;for(int y=-radius;y<=radius;++y){std::string row(static_cast<std::size_t>(width),fill);int half=radius-std::abs(y);row[static_cast<std::size_t>(radius-half)]=ink;row[static_cast<std::size_t>(radius+half)]=ink;rows.push_back(std::move(row));}return rows;}""",
        """using charm::v1n3::diamond::render_outline_diamond;
int main(){assert((render_outline_diamond(1,'#','.').value()==std::vector<std::string>{".#.","#.#",".#."}));assert(render_outline_diamond(0,'x',' ')->at(0)=="x");assert(!render_outline_diamond(-1,'x',' '));assert(!render_outline_diamond(1,'x','x'));assert(render_outline_diamond(2,'*','-')->size()==5);return 0;}""",
        ("return type is exact", "all rows have fixed width", "radius zero is one glyph", "ink and fill differ", "radius is bounded"),
        "coordinate-distance boundary placement into rectangular rows", ("outline", "symmetry", "whitespace-oracle"),
    )
    add(
        "Diamond", "layered-value-diamond", "Layered value diamond",
        "Render a filled odd-width diamond whose cell value is the one-based distance from the outside boundary, encoded as a lowercase hexadecimal digit. Outside cells are dots. Radius is from zero through 14 so every layer fits one hex digit.",
        "", "std::optional<std::vector<std::string>> render_layered_diamond(int radius)",
        """std::optional<std::vector<std::string>> charm::v1n3::diamond::render_layered_diamond(int radius){if(radius<0||radius>14)return std::nullopt;int width=2*radius+1;std::vector<std::string> out(static_cast<std::size_t>(width),std::string(static_cast<std::size_t>(width),'.'));const char* digits="0123456789abcdef";for(int y=-radius;y<=radius;++y)for(int x=-radius;x<=radius;++x){int d=std::abs(x)+std::abs(y);if(d<=radius)out[static_cast<std::size_t>(y+radius)][static_cast<std::size_t>(x+radius)]=digits[radius-d+1];}return out;}""",
        """using charm::v1n3::diamond::render_layered_diamond;
int main(){assert(render_layered_diamond(0)->at(0)=="1");assert((render_layered_diamond(1).value()==std::vector<std::string>{".1.","121",".1."}));assert(render_layered_diamond(2)->at(2)=="12321");assert(!render_layered_diamond(-1));assert(!render_layered_diamond(15));return 0;}""",
        ("outside cells are dots", "center is deepest layer", "values are lowercase hex", "shape is horizontally and vertically symmetric", "radius is bounded to digit capacity"),
        "Manhattan-depth rasterization with explicit layer alphabet", ("filled", "layer-depth", "deterministic"),
    )
    add(
        "Diamond", "strict-glyph-diamond-validator", "Strict glyph diamond validator",
        "Validate a rectangular glyph grid as a strict filled diamond: dimensions must be the same positive odd number, ink cells must be exactly those with Manhattan distance at most radius from center, and every other cell must equal fill. ink and fill must differ.",
        "", "bool is_strict_glyph_diamond(const std::vector<std::string>& rows, char ink, char fill)",
        """bool charm::v1n3::diamond::is_strict_glyph_diamond(const std::vector<std::string>& rows,char ink,char fill){if(ink==fill||rows.empty()||rows.size()%2==0)return false;std::size_t width=rows.size();for(const auto& row:rows)if(row.size()!=width)return false;long long radius=static_cast<long long>(width/2);for(std::size_t y=0;y<width;++y)for(std::size_t x=0;x<width;++x){bool inside=std::llabs(static_cast<long long>(x)-radius)+std::llabs(static_cast<long long>(y)-radius)<=radius;if(rows[y][x]!=(inside?ink:fill))return false;}return true;}""",
        """using charm::v1n3::diamond::is_strict_glyph_diamond;
int main(){assert(is_strict_glyph_diamond({".*.","***",".*."},'*','.'));assert(is_strict_glyph_diamond({"x"},'x',' '));assert(!is_strict_glyph_diamond({},'*','.'));assert(!is_strict_glyph_diamond({"**","**"},'*','.'));assert(!is_strict_glyph_diamond({".*.","**.",".*."},'*','.'));return 0;}""",
        ("dimensions are positive odd square", "glyphs are exhaustive", "center and axes are ink", "corners are fill except radius zero", "ink and fill differ"),
        "exhaustive coordinate oracle for exact glyph membership", ("validator", "return-symbol", "boundary-character"),
    )

    # Grade School: self-contained ordered records, cutlines, and conflict-aware merge.
    add(
        "Grade School", "unique-student-roster", "Unique student roster",
        "Build a roster from records with nonempty student IDs, grades 1 through 12, and scores 0 through 100. Student IDs must be unique. Return records ordered by ascending grade, descending score, then ID.",
        "struct StudentRecord { std::string id; int grade; int score; };", "std::optional<std::vector<StudentRecord>> ordered_unique_roster(const std::vector<StudentRecord>& records)",
        """std::optional<std::vector<charm::v1n3::grade_school::StudentRecord>> charm::v1n3::grade_school::ordered_unique_roster(const std::vector<charm::v1n3::grade_school::StudentRecord>& records){std::set<std::string> ids;for(const auto& r:records)if(r.id.empty()||r.grade<1||r.grade>12||r.score<0||r.score>100||!ids.insert(r.id).second)return std::nullopt;auto out=records;std::sort(out.begin(),out.end(),[](const auto& a,const auto& b){if(a.grade!=b.grade)return a.grade<b.grade;if(a.score!=b.score)return a.score>b.score;return a.id<b.id;});return out;}""",
        """using namespace charm::v1n3::grade_school;
int main(){auto r=ordered_unique_roster({{"b",2,90},{"a",1,80},{"c",2,90}});assert(r&&r->at(0).id=="a"&&r->at(1).id=="b"&&r->at(2).id=="c");assert(ordered_unique_roster({})->empty());assert(!ordered_unique_roster({{"",1,1}}));assert(!ordered_unique_roster({{"a",1,1},{"a",2,2}}));assert(!ordered_unique_roster({{"a",13,1}}));return 0;}""",
        ("header directly provides set", "student IDs are unique", "grade and score ranges are closed", "ordering has three keys", "empty roster is valid"),
        "self-contained uniqueness validation followed by deterministic multi-key sort", ("direct-include", "set", "roster"),
    )
    add(
        "Grade School", "promotion-cutline-groups", "Promotion cutline groups",
        "For each grade, promote the top requested count by score. A tie at the final promoted score expands the promoted set to include every tied student. Inputs require unique nonempty IDs, valid grades, valid scores, and valid requested grade keys. Return promoted IDs in lexical order.",
        "struct GradeScore { std::string id; int grade; int score; };", "std::optional<std::vector<std::string>> promotion_cutline_ids(const std::vector<GradeScore>& scores, const std::map<int,std::size_t>& requested)",
        """std::optional<std::vector<std::string>> charm::v1n3::grade_school::promotion_cutline_ids(const std::vector<charm::v1n3::grade_school::GradeScore>& scores,const std::map<int,std::size_t>& requested){std::set<std::string> ids;std::map<int,std::vector<GradeScore>> groups;for(const auto& s:scores)if(s.id.empty()||s.grade<1||s.grade>12||s.score<0||s.score>100||!ids.insert(s.id).second)return std::nullopt;else groups[s.grade].push_back(s);for(const auto& item:requested)if(item.first<1||item.first>12)return std::nullopt;std::vector<std::string> result;for(auto& group:groups){std::size_t count=requested.count(group.first)?requested.at(group.first):0;if(count==0)continue;auto& v=group.second;std::sort(v.begin(),v.end(),[](const auto&a,const auto&b){return a.score>b.score;});int cut=v[std::min(count,v.size())-1].score;for(const auto& s:v)if(s.score>=cut)result.push_back(s.id);}std::sort(result.begin(),result.end());return result;}""",
        """using namespace charm::v1n3::grade_school;
int main(){auto r=promotion_cutline_ids({{"a",1,90},{"b",1,80},{"c",1,80},{"d",2,70}},{{1,2},{2,0}});assert(r&&*r==(std::vector<std::string>{"a","b","c"}));assert(promotion_cutline_ids({},{})->empty());assert(!promotion_cutline_ids({{"a",0,1}},{}));assert(!promotion_cutline_ids({{"a",1,1},{"a",1,2}},{}));assert(!promotion_cutline_ids({},{{13,1}}));return 0;}""",
        ("ties expand the cutline", "missing requests mean zero", "IDs are globally unique", "unknown grades reject", "output is lexical"),
        "per-grade cutline discovery with tie closure", ("promotion", "tie", "ordering"),
    )
    add(
        "Grade School", "conflict-aware-transcript-merge", "Conflict-aware transcript merge",
        "Merge two transcript snapshots keyed by student ID. Identical records coalesce; a differing grade or score for the same ID is a conflict and rejects the merge. Records require valid IDs, grades, and scores. Return merged records ordered by ID.",
        "struct TranscriptRow { std::string id; int grade; int score; };", "std::optional<std::vector<TranscriptRow>> merge_identical_transcripts(const std::vector<TranscriptRow>& left, const std::vector<TranscriptRow>& right)",
        """std::optional<std::vector<charm::v1n3::grade_school::TranscriptRow>> charm::v1n3::grade_school::merge_identical_transcripts(const std::vector<charm::v1n3::grade_school::TranscriptRow>& left,const std::vector<charm::v1n3::grade_school::TranscriptRow>& right){std::map<std::string,TranscriptRow> rows;for(const auto* source:{&left,&right})for(const auto& row:*source){if(row.id.empty()||row.grade<1||row.grade>12||row.score<0||row.score>100)return std::nullopt;auto [it,inserted]=rows.emplace(row.id,row);if(!inserted&&(it->second.grade!=row.grade||it->second.score!=row.score))return std::nullopt;}std::vector<TranscriptRow> out;for(const auto& item:rows)out.push_back(item.second);return out;}""",
        """using namespace charm::v1n3::grade_school;
int main(){auto r=merge_identical_transcripts({{"b",2,8},{"a",1,9}},{{"a",1,9},{"c",3,7}});assert(r&&r->size()==3&&r->at(0).id=="a");assert(merge_identical_transcripts({},{})->empty());assert(!merge_identical_transcripts({{"a",1,1}},{{"a",2,1}}));assert(!merge_identical_transcripts({{"a",1,1},{"a",1,2}},{}));assert(!merge_identical_transcripts({{"",1,1}},{}));return 0;}""",
        ("identical duplicates coalesce", "conflicts reject", "validation covers both sides", "output is ID ordered", "empty inputs are valid"),
        "ordered-map coalescing with exact record conflict detection", ("merge", "duplicate-invariant", "header-self-contained"),
    )

    # Kindergarten Garden: explicit plant domain, mapping order, and allocation validation.
    add(
        "Kindergarten Garden", "typed-plant-row-parser", "Typed plant row parser",
        "Parse two equal-width plant rows into the exact PlantCode enum and assign each consecutive pair of columns to one child. Children are supplied in mapping order and count must equal width/2. Reject odd widths, invalid plant bytes, duplicate or empty child names, and inconsistent dimensions.",
        "enum class PlantCode { clover, grass, radish, violet }; using ChildPlants = std::pair<std::string,std::array<PlantCode,4>>;", "std::optional<std::vector<ChildPlants>> parse_typed_garden(std::string_view top, std::string_view bottom, const std::vector<std::string>& children)",
        """std::optional<std::vector<charm::v1n3::kindergarten_garden::ChildPlants>> charm::v1n3::kindergarten_garden::parse_typed_garden(std::string_view top,std::string_view bottom,const std::vector<std::string>& children){if(top.size()!=bottom.size()||top.size()%2!=0||children.size()!=top.size()/2)return std::nullopt;std::set<std::string> names;auto decode=[](char c)->std::optional<PlantCode>{if(c=='C')return PlantCode::clover;if(c=='G')return PlantCode::grass;if(c=='R')return PlantCode::radish;if(c=='V')return PlantCode::violet;return std::nullopt;};std::vector<ChildPlants> out;for(std::size_t i=0;i<children.size();++i){if(children[i].empty()||!names.insert(children[i]).second)return std::nullopt;auto a=decode(top[2*i]),b=decode(top[2*i+1]),c=decode(bottom[2*i]),d=decode(bottom[2*i+1]);if(!a||!b||!c||!d)return std::nullopt;out.push_back({children[i],{*a,*b,*c,*d}});}return out;}""",
        """using namespace charm::v1n3::kindergarten_garden;
int main(){auto r=parse_typed_garden("RCGV","GCVR",{"Ada","Bob"});assert(r&&r->size()==2&&r->at(0).second[0]==PlantCode::radish&&r->at(1).first=="Bob");assert(parse_typed_garden("","",{})->empty());assert(!parse_typed_garden("C","C",{}));assert(!parse_typed_garden("XX","CC",{"A"}));assert(!parse_typed_garden("CC","GG",{"A","B"}));return 0;}""",
        ("enum names are exact", "two rows have equal even width", "children follow supplied order", "plant bytes are closed-domain", "names are unique"),
        "direct byte-to-enum decoding with positional two-row grouping", ("enum-api", "direct-include", "mapping-order"),
    )
    add(
        "Kindergarten Garden", "rotating-cup-assignment", "Rotating cup assignment",
        "Assign a flat sequence of plant labels to children in rotating order beginning at signed start_child. Child names must be unique and nonempty, labels must be nonempty, and no assignment is possible when children are empty unless labels are also empty. Return each child and its assigned labels in original child order.",
        "", "std::optional<std::vector<std::pair<std::string,std::vector<std::string>>>> assign_rotating_cups(const std::vector<std::string>& children, const std::vector<std::string>& labels, long long start_child)",
        """std::optional<std::vector<std::pair<std::string,std::vector<std::string>>>> charm::v1n3::kindergarten_garden::assign_rotating_cups(const std::vector<std::string>& children,const std::vector<std::string>& labels,long long start_child){std::set<std::string> names;for(const auto& child:children)if(child.empty()||!names.insert(child).second)return std::nullopt;for(const auto& label:labels)if(label.empty())return std::nullopt;if(children.empty()){if(!labels.empty())return std::nullopt;return std::vector<std::pair<std::string,std::vector<std::string>>>{};}long long n=static_cast<long long>(children.size());long long start=start_child%n;if(start<0)start+=n;std::vector<std::pair<std::string,std::vector<std::string>>> out;for(const auto& child:children)out.push_back({child,{}});for(std::size_t i=0;i<labels.size();++i)out[static_cast<std::size_t>((start+static_cast<long long>(i))%n)].second.push_back(labels[i]);return out;}""",
        """using charm::v1n3::kindergarten_garden::assign_rotating_cups;
int main(){auto r=assign_rotating_cups({"A","B","C"},{"x","y","z","w"},-1);assert((r&&r->at(2).second==std::vector<std::string>{"x","w"}&&r->at(0).second==std::vector<std::string>{"y"}));assert(assign_rotating_cups({}, {}, 9)->empty());assert(!assign_rotating_cups({}, {"x"}, 0));assert(!assign_rotating_cups({"A","A"},{},0));assert(!assign_rotating_cups({"A"},{""},0));return 0;}""",
        ("signed start normalizes", "children retain input order", "labels retain per-child order", "empty domain behavior is explicit", "names and labels are validated"),
        "normalized round-robin index assignment into stable child buckets", ("rotation", "mapping", "invalid-input"),
    )
    add(
        "Kindergarten Garden", "garden-capacity-audit", "Garden capacity audit",
        "Audit named child plots against per-plant capacities. Child names must be unique, plant names nonempty, counts nonnegative, and a plant may appear at most once per child. Every allocated plant requires a declared nonnegative capacity. Return plants exceeding total capacity ordered by name.",
        "struct PlantCount { std::string plant; int count; }; struct ChildPlot { std::string child; std::vector<PlantCount> plants; };", "std::optional<std::vector<std::pair<std::string,int>>> audit_garden_capacity(const std::vector<ChildPlot>& plots, const std::map<std::string,int>& capacity)",
        """std::optional<std::vector<std::pair<std::string,int>>> charm::v1n3::kindergarten_garden::audit_garden_capacity(const std::vector<charm::v1n3::kindergarten_garden::ChildPlot>& plots,const std::map<std::string,int>& capacity){for(const auto& c:capacity)if(c.first.empty()||c.second<0)return std::nullopt;std::set<std::string> children;std::map<std::string,int> totals;for(const auto& plot:plots){if(plot.child.empty()||!children.insert(plot.child).second)return std::nullopt;std::set<std::string> seen;for(const auto& p:plot.plants){if(p.plant.empty()||p.count<0||capacity.count(p.plant)==0||!seen.insert(p.plant).second)return std::nullopt;if(totals[p.plant]>std::numeric_limits<int>::max()-p.count)return std::nullopt;totals[p.plant]+=p.count;}}std::vector<std::pair<std::string,int>> out;for(const auto& p:totals)if(p.second>capacity.at(p.first))out.emplace_back(p.first,p.second-capacity.at(p.first));return out;}""",
        """using namespace charm::v1n3::kindergarten_garden;
int main(){auto r=audit_garden_capacity({{"A",{{"C",2},{"R",1}}},{"B",{{"C",2}}}},{{"C",3},{"R",2}});assert(r&&*r==(std::vector<std::pair<std::string,int>>{{"C",1}}));assert(audit_garden_capacity({},{})->empty());assert(!audit_garden_capacity({{"A",{{"X",1}}}},{}));assert(!audit_garden_capacity({{"A",{{"X",1},{"X",1}}}},{{"X",3}}));assert(!audit_garden_capacity({{"A",{}},{"A",{}}},{}));return 0;}""",
        ("children are unique", "plant appears once per child", "capacity domain is explicit", "counts and capacities are nonnegative", "excess output is lexical"),
        "nested identity validation and overflow-checked capacity aggregation", ("capacity", "domain-types", "direct-includes"),
    )

    # Linked List: unique ownership, read-before-unlink, and index-cycle validation.
    add(
        "Linked List", "owned-chain-erasures", "Owned chain erasures",
        "Build a singly linked chain with unique ownership, then erase zero-based positions sequentially. Each position is interpreted in the current chain; an out-of-range position rejects. The implementation must capture the successor before destroying the selected link. Return removed values followed by the remaining values.",
        "struct ChainEraseResult { std::vector<int> removed; std::vector<int> remaining; };", "std::optional<ChainEraseResult> erase_owned_chain_positions(const std::vector<int>& values, const std::vector<std::size_t>& positions)",
        """std::optional<charm::v1n3::linked_list::ChainEraseResult> charm::v1n3::linked_list::erase_owned_chain_positions(const std::vector<int>& values,const std::vector<std::size_t>& positions){struct Node{int value;std::unique_ptr<Node> next;explicit Node(int v):value(v){}};std::unique_ptr<Node> head;Node* tail=nullptr;for(int value:values){auto node=std::make_unique<Node>(value);Node* raw=node.get();if(tail)tail->next=std::move(node);else head=std::move(node);tail=raw;}ChainEraseResult result;std::size_t size=values.size();for(std::size_t position:positions){if(position>=size)return std::nullopt;std::unique_ptr<Node>* link=&head;for(std::size_t i=0;i<position;++i)link=&(*link)->next;result.removed.push_back((*link)->value);std::unique_ptr<Node> successor=std::move((*link)->next);*link=std::move(successor);--size;}for(Node* node=head.get();node;node=node->next.get())result.remaining.push_back(node->value);return result;}""",
        """using charm::v1n3::linked_list::erase_owned_chain_positions;
int main(){auto r=erase_owned_chain_positions({10,20,30,40},{1,1});assert(r&&r->removed==(std::vector<int>{20,30})&&r->remaining==(std::vector<int>{10,40}));assert(erase_owned_chain_positions({},{})->remaining.empty());assert(!erase_owned_chain_positions({}, {0}));assert(erase_owned_chain_positions({1},{0})->remaining.empty());assert(!erase_owned_chain_positions({1,2},{2}));return 0;}""",
        ("ownership uses unique_ptr", "positions use current chain", "successor is read before unlink", "empty and singleton chains are covered", "out-of-range rejects"),
        "pointer-to-owned-link traversal with successor capture before destruction", ("unique-ptr", "read-before-unlink", "sanitizer"),
    )
    add(
        "Linked List", "stable-chain-partition", "Stable chain partition",
        "Build an owned chain and stably partition its nodes around pivot without copying node values: values less than pivot precede values greater than or equal to pivot while relative order in each group remains unchanged. Return the resulting sequence and the number of relinked nodes.",
        "struct ChainPartition { std::vector<int> values; std::size_t relinked; };", "ChainPartition stable_partition_owned_chain(const std::vector<int>& values, int pivot)",
        """charm::v1n3::linked_list::ChainPartition charm::v1n3::linked_list::stable_partition_owned_chain(const std::vector<int>& values,int pivot){struct Node{int value;std::unique_ptr<Node> next;explicit Node(int v):value(v){}};std::unique_ptr<Node> input;for(auto it=values.rbegin();it!=values.rend();++it){auto n=std::make_unique<Node>(*it);n->next=std::move(input);input=std::move(n);}std::unique_ptr<Node> low,high;Node* low_tail=nullptr;Node* high_tail=nullptr;std::size_t moved=0;while(input){auto node=std::move(input);input=std::move(node->next);Node* raw=node.get();if(node->value<pivot){if(low_tail)low_tail->next=std::move(node);else low=std::move(node);low_tail=raw;}else{if(high_tail)high_tail->next=std::move(node);else high=std::move(node);high_tail=raw;}++moved;}if(low_tail)low_tail->next=std::move(high);else low=std::move(high);ChainPartition result{{},moved};for(Node* n=low.get();n;n=n->next.get())result.values.push_back(n->value);return result;}""",
        """using charm::v1n3::linked_list::stable_partition_owned_chain;
int main(){auto r=stable_partition_owned_chain({3,1,2,1,4},3);assert(r.values==(std::vector<int>{1,2,1,3,4})&&r.relinked==5);assert(stable_partition_owned_chain({},0).relinked==0);assert(stable_partition_owned_chain({1},2).values==std::vector<int>{1});assert(stable_partition_owned_chain({2,3},0).values==(std::vector<int>{2,3}));assert(stable_partition_owned_chain({-1,2},1).values==(std::vector<int>{-1,2}));return 0;}""",
        ("values are not copied during relink", "partition is stable", "every node is relinked once", "empty and singleton work", "pivot belongs to high group"),
        "two-tail ownership extraction followed by constant-time chain concatenation", ("ownership", "stable-partition", "lifetime"),
    )
    add(
        "Linked List", "indexed-chain-cycle-entry", "Indexed chain cycle entry",
        "Validate an indexed next-link table and find the cycle entry reachable from head using tortoise-hare traversal. -1 denotes null. Invalid head or link indices reject the table; a valid acyclic chain returns an engaged outer optional containing an empty inner optional.",
        "", "std::optional<std::optional<std::size_t>> indexed_chain_cycle_entry(const std::vector<int>& next, int head)",
        """std::optional<std::optional<std::size_t>> charm::v1n3::linked_list::indexed_chain_cycle_entry(const std::vector<int>& next,int head){if(head<-1||head>=static_cast<int>(next.size()))return std::nullopt;for(int link:next)if(link<-1||link>=static_cast<int>(next.size()))return std::nullopt;if(head==-1)return std::optional<std::size_t>{};auto step=[&](int x){return x<0?-1:next[static_cast<std::size_t>(x)];};int slow=head,fast=head;do{slow=step(slow);fast=step(step(fast));if(slow<0||fast<0)return std::optional<std::size_t>{};}while(slow!=fast);slow=head;while(slow!=fast){slow=step(slow);fast=step(fast);}return std::optional<std::size_t>{static_cast<std::size_t>(slow)};}""",
        """using charm::v1n3::linked_list::indexed_chain_cycle_entry;
int main(){auto r=indexed_chain_cycle_entry({1,2,1},0);assert(r&&*r&&**r==1);auto a=indexed_chain_cycle_entry({1,-1},0);assert(a&&!*a);auto e=indexed_chain_cycle_entry({},-1);assert(e&&!*e);assert(!indexed_chain_cycle_entry({2},0));assert(!indexed_chain_cycle_entry({},0));return 0;}""",
        ("outer optional reports table validity", "inner optional reports cycle", "minus one is null", "all links are validated", "cycle search is constant space"),
        "validated index graph with Floyd meeting and entry phases", ("cycle", "index-validation", "constant-space"),
    )

    # Parallel Letter Frequency: explicit map types, partitions, zero-worker policy, and race-free joins.
    add(
        "Parallel Letter Frequency", "ascii-sharded-frequency", "ASCII sharded frequency",
        "Count ASCII letters case-insensitively across input strings with exactly min(worker_count,input_count) asynchronous shards. The exact result type is std::unordered_map<char,std::size_t>. worker_count zero rejects; empty input with positive workers returns an empty map. Non-ASCII bytes and nonletters are ignored.",
        "", "std::optional<std::unordered_map<char,std::size_t>> sharded_ascii_frequency(const std::vector<std::string>& inputs, std::size_t worker_count)",
        """std::optional<std::unordered_map<char,std::size_t>> charm::v1n3::parallel_letter_frequency::sharded_ascii_frequency(const std::vector<std::string>& inputs,std::size_t worker_count){if(worker_count==0)return std::nullopt;if(inputs.empty())return std::unordered_map<char,std::size_t>{};std::size_t workers=std::min(worker_count,inputs.size());std::vector<std::future<std::unordered_map<char,std::size_t>>> jobs;for(std::size_t w=0;w<workers;++w)jobs.push_back(std::async(std::launch::async,[&,w]{std::unordered_map<char,std::size_t> local;for(std::size_t i=w;i<inputs.size();i+=workers)for(unsigned char c:inputs[i])if(c<128&&std::isalpha(c))++local[static_cast<char>(std::tolower(c))];return local;}));std::unordered_map<char,std::size_t> result;for(auto& job:jobs)for(const auto& item:job.get())result[item.first]+=item.second;return result;}""",
        """using charm::v1n3::parallel_letter_frequency::sharded_ascii_frequency;
int main(){auto r=sharded_ascii_frequency({"Aa!","bA","\xC3\xA9"},2);assert(r&&r->at('a')==3&&r->at('b')==1&&r->size()==2);assert(sharded_ascii_frequency({},3)->empty());assert(!sharded_ascii_frequency({},0));assert(sharded_ascii_frequency({"123"},1)->empty());assert(sharded_ascii_frequency({"Z"},9)->at('z')==1);return 0;}""",
        ("unordered_map type is exact", "zero workers reject", "worker count is capped with matching size types", "shards own local maps", "join is deterministic in counts"),
        "strided local hash maps joined after futures complete", ("unordered-map", "partition-join", "race-free"),
    )
    add(
        "Parallel Letter Frequency", "partitioned-letter-runs", "Partitioned letter runs",
        "For each input string, compute its longest contiguous run of the same ASCII letter ignoring case, without joining across string boundaries. Process strings through bounded asynchronous partitions and return one length per input in original order. worker_count zero rejects.",
        "", "std::optional<std::vector<std::size_t>> parallel_longest_letter_runs(const std::vector<std::string>& inputs, std::size_t worker_count)",
        """std::optional<std::vector<std::size_t>> charm::v1n3::parallel_letter_frequency::parallel_longest_letter_runs(const std::vector<std::string>& inputs,std::size_t worker_count){if(worker_count==0)return std::nullopt;std::vector<std::size_t> result(inputs.size());if(inputs.empty())return result;std::size_t workers=std::min(worker_count,inputs.size());std::vector<std::future<void>> jobs;for(std::size_t w=0;w<workers;++w)jobs.push_back(std::async(std::launch::async,[&,w]{for(std::size_t i=w;i<inputs.size();i+=workers){std::size_t best=0,run=0;int previous=-1;for(unsigned char c:inputs[i]){int current=c<128&&std::isalpha(c)?std::tolower(c):-1;if(current>=0&&current==previous)++run;else run=current>=0?1U:0U;best=std::max(best,run);previous=current;}result[i]=best;}}));for(auto& job:jobs)job.get();return result;}""",
        """using charm::v1n3::parallel_letter_frequency::parallel_longest_letter_runs;
int main(){assert((parallel_longest_letter_runs({"aaA-bb","xyz","111"},2).value()==std::vector<std::size_t>{3,1,0}));assert(parallel_longest_letter_runs({},1)->empty());assert(!parallel_longest_letter_runs({"a"},0));assert(parallel_longest_letter_runs({"ZZ"},9)->at(0)==2);assert(parallel_longest_letter_runs({"aA"},1)->at(0)==2);return 0;}""",
        ("runs never cross inputs", "case folds ASCII only", "nonletters break runs", "each output slot has one writer", "zero workers reject"),
        "disjoint-index asynchronous scans with local run state", ("partition", "disjoint-write", "type-conversion"),
    )
    add(
        "Parallel Letter Frequency", "deterministic-shard-top-letter", "Deterministic shard top letter",
        "Count lowercase ASCII letters over byte shards and return the most frequent letter and count. Each shard is processed asynchronously; ties select the lexically smaller letter. worker_count must be positive. If there are no lowercase letters, return an empty inner optional.",
        "", "std::optional<std::optional<std::pair<char,std::size_t>>> parallel_top_lowercase(const std::vector<std::string>& shards, std::size_t worker_count)",
        """std::optional<std::optional<std::pair<char,std::size_t>>> charm::v1n3::parallel_letter_frequency::parallel_top_lowercase(const std::vector<std::string>& shards,std::size_t worker_count){if(worker_count==0)return std::nullopt;if(shards.empty())return std::optional<std::pair<char,std::size_t>>{};std::size_t workers=std::min(worker_count,shards.size());std::vector<std::future<std::array<std::size_t,26>>> jobs;for(std::size_t w=0;w<workers;++w)jobs.push_back(std::async(std::launch::async,[&,w]{std::array<std::size_t,26> counts{};for(std::size_t i=w;i<shards.size();i+=workers)for(unsigned char c:shards[i])if(c>='a'&&c<='z')++counts[c-'a'];return counts;}));std::array<std::size_t,26> total{};for(auto& job:jobs){auto part=job.get();for(std::size_t i=0;i<26;++i)total[i]+=part[i];}auto it=std::max_element(total.begin(),total.end());if(*it==0)return std::optional<std::pair<char,std::size_t>>{};return std::optional<std::pair<char,std::size_t>>{{static_cast<char>('a'+std::distance(total.begin(),it)),*it}};}""",
        """using charm::v1n3::parallel_letter_frequency::parallel_top_lowercase;
int main(){auto r=parallel_top_lowercase({"bba","acc"},2);assert((r&&*r&&**r==std::pair<char,std::size_t>('a',2)));auto e=parallel_top_lowercase({"ABC"},1);assert(e&&!*e);assert(!parallel_top_lowercase({},0));auto n=parallel_top_lowercase({},2);assert(n&&!*n);assert(parallel_top_lowercase({"zz"},9)->value().first=='z');return 0;}""",
        ("only lowercase bytes count", "tie breaks lexically", "outer optional is configuration validity", "inner optional is data presence", "partitions are local"),
        "fixed-array shard counts with ordered deterministic reduction", ("array-count", "deterministic-reduce", "zero-worker"),
    )

    # Phone Number: constructor-to-member transfer, normalization boundaries, and prefix grouping.
    add(
        "Phone Number", "member-backed-phone-parser", "Member-backed phone parser",
        "Parse ASCII phone text into the exact NormalizedPhone class. Ten national digits are accepted; eleven digits are accepted only when the first is 1 and that prefix is removed. A single x or X introduces a nonempty digit-only extension. Area and exchange codes may not begin with 0 or 1. The constructor must transfer values into member state exposed by const accessors.",
        "class NormalizedPhone { public: NormalizedPhone(std::string national_digits, std::string extension_digits); const std::string& digits() const; const std::string& extension() const; private: std::string digits_; std::string extension_; };",
        "std::optional<NormalizedPhone> parse_normalized_phone(std::string_view text)",
        """std::optional<charm::v1n3::phone_number::NormalizedPhone> charm::v1n3::phone_number::parse_normalized_phone(std::string_view text){std::string main,ext;bool in_extension=false;for(char raw:text){unsigned char c=static_cast<unsigned char>(raw);if(raw=='x'||raw=='X'){if(in_extension)return std::nullopt;in_extension=true;continue;}if(std::isdigit(c)){(in_extension?ext:main).push_back(raw);}else if(std::isalpha(c))return std::nullopt;}if(in_extension&&ext.empty())return std::nullopt;if(main.size()==11&&main.front()=='1')main.erase(main.begin());if(main.size()!=10||main[0]<'2'||main[3]<'2')return std::nullopt;return NormalizedPhone(main,ext);}
charm::v1n3::phone_number::NormalizedPhone::NormalizedPhone(std::string national_digits,std::string extension_digits):digits_(std::move(national_digits)),extension_(std::move(extension_digits)){}
const std::string& charm::v1n3::phone_number::NormalizedPhone::digits() const{return digits_;}
const std::string& charm::v1n3::phone_number::NormalizedPhone::extension() const{return extension_;}""",
        """using namespace charm::v1n3::phone_number;
int main(){auto p=parse_normalized_phone("+1 (223) 456-7890 x42");assert(p&&p->digits()=="2234567890"&&p->extension()=="42");assert(parse_normalized_phone("2234567890")->extension().empty());assert(!parse_normalized_phone("1234567890"));assert(!parse_normalized_phone("2231567890"));assert(!parse_normalized_phone("2234567890x"));return 0;}""",
        ("member state is observable through const accessors", "country prefix is exactly one", "area and exchange starts are bounded", "extension syntax is unique", "alphabetic noise rejects"),
        "stateful ASCII parser followed by explicit constructor member transfer", ("member-state", "shadowing-mutation", "invalid-optional"),
    )
    add(
        "Phone Number", "preserving-phone-redaction", "Preserving phone redaction",
        "Redact a phone-like string by preserving separators and the final visible_digits decimal digits while replacing every earlier digit with mask. Return the exact RedactedPhone result containing both the transformed text and hidden digit count. visible_digits may not exceed the total digit count and mask must not be a decimal digit. Non-digit bytes are preserved exactly.",
        "struct RedactedPhone { std::string text; std::size_t hidden_digits; };", "std::optional<RedactedPhone> redact_phone_digits(std::string_view text, std::size_t visible_digits, char mask)",
        """std::optional<charm::v1n3::phone_number::RedactedPhone> charm::v1n3::phone_number::redact_phone_digits(std::string_view text,std::size_t visible_digits,char mask){if(std::isdigit(static_cast<unsigned char>(mask)))return std::nullopt;std::size_t total=0;for(char c:text)if(std::isdigit(static_cast<unsigned char>(c)))++total;if(visible_digits>total)return std::nullopt;std::size_t hide=total-visible_digits,seen=0;std::string out(text);for(char& c:out)if(std::isdigit(static_cast<unsigned char>(c))){if(seen<hide)c=mask;++seen;}return RedactedPhone{std::move(out),hide};}""",
        """using namespace charm::v1n3::phone_number;
int main(){auto a=redact_phone_digits("(223) 456-7890",4,'*');assert(a&&a->text=="(***) ***-7890"&&a->hidden_digits==6);auto b=redact_phone_digits("abc",0,'#');assert(b&&b->text=="abc"&&b->hidden_digits==0);auto c=redact_phone_digits("12",2,'#');assert(c&&c->text=="12"&&c->hidden_digits==0);assert(!redact_phone_digits("12",3,'#'));assert(!redact_phone_digits("12",1,'7'));return 0;}""",
        ("result reports hidden cardinality", "separators preserve byte identity", "last digits remain visible", "mask cannot be a digit", "visible count is bounded"),
        "two-pass digit cardinality with explicit result topology and stable masking", ("redaction", "result-struct", "format-preserving"),
    )
    add(
        "Phone Number", "dial-prefix-buckets", "Dial prefix buckets",
        "Group already-normalized digit strings by the longest matching declared dial prefix. Prefixes must be nonempty digit strings with no duplicates; numbers must contain only digits. A number with no prefix match rejects. Return buckets ordered by prefix, with numbers retaining input order.",
        "", "std::optional<std::map<std::string,std::vector<std::string>>> bucket_by_longest_prefix(const std::vector<std::string>& numbers, const std::vector<std::string>& prefixes)",
        """std::optional<std::map<std::string,std::vector<std::string>>> charm::v1n3::phone_number::bucket_by_longest_prefix(const std::vector<std::string>& numbers,const std::vector<std::string>& prefixes){std::set<std::string> unique;for(const auto& prefix:prefixes){if(prefix.empty()||!std::all_of(prefix.begin(),prefix.end(),[](unsigned char c){return std::isdigit(c);})||!unique.insert(prefix).second)return std::nullopt;}std::map<std::string,std::vector<std::string>> out;for(const auto& number:numbers){if(number.empty()||!std::all_of(number.begin(),number.end(),[](unsigned char c){return std::isdigit(c);}))return std::nullopt;const std::string* best=nullptr;for(const auto& prefix:prefixes)if(number.rfind(prefix,0)==0&&(!best||prefix.size()>best->size()))best=&prefix;if(!best)return std::nullopt;out[*best].push_back(number);}return out;}""",
        """using charm::v1n3::phone_number::bucket_by_longest_prefix;
int main(){auto r=bucket_by_longest_prefix({"1202","1299","441"},{"1","12","44"});assert(r&&r->at("12")==std::vector<std::string>({"1202","1299"})&&r->at("44")==std::vector<std::string>({"441"}));assert(bucket_by_longest_prefix({},{})->empty());assert(!bucket_by_longest_prefix({"99"},{"1"}));assert(!bucket_by_longest_prefix({"1a"},{"1"}));assert(!bucket_by_longest_prefix({}, {"1","1"}));return 0;}""",
        ("longest prefix wins", "prefix domain is unique", "all text is digit-only", "unmatched numbers reject", "bucket order and item order are deterministic"),
        "validated prefix dictionary with longest-start match selection", ("prefix", "grouping", "constructor-state-alternative"),
    )

    # Spiral Matrix: exact rectangular shapes, complete fill, and path validation.
    add(
        "Spiral Matrix", "corner-directed-spiral-path", "Corner-directed spiral path",
        "Return every coordinate of a rows-by-columns rectangle exactly once in clockwise spiral order, starting from the declared Corner. Zero in either dimension returns an empty path. Dimensions whose product overflows size_t reject.",
        "enum class Corner { top_left, top_right, bottom_right, bottom_left };", "std::optional<std::vector<std::pair<std::size_t,std::size_t>>> clockwise_spiral_path(std::size_t rows, std::size_t columns, Corner start)",
        """std::optional<std::vector<std::pair<std::size_t,std::size_t>>> charm::v1n3::spiral_matrix::clockwise_spiral_path(std::size_t rows,std::size_t columns,charm::v1n3::spiral_matrix::Corner start){if(rows!=0&&columns>std::numeric_limits<std::size_t>::max()/rows)return std::nullopt;if(rows==0||columns==0)return std::vector<std::pair<std::size_t,std::size_t>>{};std::vector<std::vector<bool>> seen(rows,std::vector<bool>(columns));std::array<int,4> dr{0,1,0,-1},dc{1,0,-1,0};std::size_t r=0,c=0;int direction=0;if(start==Corner::top_right){c=columns-1;direction=1;}else if(start==Corner::bottom_right){r=rows-1;c=columns-1;direction=2;}else if(start==Corner::bottom_left){r=rows-1;direction=3;}std::vector<std::pair<std::size_t,std::size_t>> out;out.reserve(rows*columns);for(std::size_t count=0;count<rows*columns;++count){out.emplace_back(r,c);seen[r][c]=true;long long nr=static_cast<long long>(r)+dr[direction],nc=static_cast<long long>(c)+dc[direction];if(nr<0||nc<0||nr>=static_cast<long long>(rows)||nc>=static_cast<long long>(columns)||seen[static_cast<std::size_t>(nr)][static_cast<std::size_t>(nc)]){direction=(direction+1)%4;nr=static_cast<long long>(r)+dr[direction];nc=static_cast<long long>(c)+dc[direction];}r=static_cast<std::size_t>(nr);c=static_cast<std::size_t>(nc);}return out;}""",
        """using namespace charm::v1n3::spiral_matrix;
int main(){assert((clockwise_spiral_path(2,3,Corner::top_left).value()==std::vector<std::pair<std::size_t,std::size_t>>{{0,0},{0,1},{0,2},{1,2},{1,1},{1,0}}));assert(clockwise_spiral_path(0,3,Corner::top_left)->empty());assert((clockwise_spiral_path(1,1,Corner::bottom_right)->at(0)==std::pair<std::size_t,std::size_t>(0,0)));assert((clockwise_spiral_path(2,2,Corner::top_right)->front()==std::pair<std::size_t,std::size_t>(0,1)));assert(clockwise_spiral_path(2,1,Corner::bottom_left)->size()==2);return 0;}""",
        ("return shape is explicit", "zero dimensions are empty", "all cells appear once", "corner controls initial coordinate and direction", "product overflow rejects"),
        "visited-grid directional walker with clockwise turn rule", ("rectangular", "coordinate-path", "output-budget"),
    )
    add(
        "Spiral Matrix", "value-fed-spiral-fill", "Value-fed spiral fill",
        "Fill a rows-by-columns integer matrix in clockwise top-left spiral order from values. The values count must equal rows*columns exactly; zero dimensions require zero values. Reject product overflow and return an explicit rectangular matrix.",
        "", "std::optional<std::vector<std::vector<int>>> fill_spiral_from_values(std::size_t rows, std::size_t columns, const std::vector<int>& values)",
        """std::optional<std::vector<std::vector<int>>> charm::v1n3::spiral_matrix::fill_spiral_from_values(std::size_t rows,std::size_t columns,const std::vector<int>& values){if(rows!=0&&columns>std::numeric_limits<std::size_t>::max()/rows)return std::nullopt;if(values.size()!=rows*columns)return std::nullopt;std::vector<std::vector<int>> matrix(rows,std::vector<int>(columns));if(values.empty())return matrix;std::size_t top=0,bottom=rows-1,left=0,right=columns-1,index=0;while(top<=bottom&&left<=right){for(std::size_t c=left;c<=right;++c)matrix[top][c]=values[index++];if(++top>bottom)break;for(std::size_t r=top;r<=bottom;++r)matrix[r][right]=values[index++];if(right--==0||left>right)break;for(std::size_t c=right+1;c-->left;)matrix[bottom][c]=values[index++];if(bottom--==0||top>bottom)break;for(std::size_t r=bottom+1;r-->top;)matrix[r][left]=values[index++];++left;}return matrix;}""",
        """using charm::v1n3::spiral_matrix::fill_spiral_from_values;
int main(){assert((fill_spiral_from_values(2,3,{1,2,3,4,5,6}).value()==std::vector<std::vector<int>>{{1,2,3},{6,5,4}}));assert(fill_spiral_from_values(0,3,{})->empty());assert(!fill_spiral_from_values(1,2,{1}));assert(fill_spiral_from_values(1,3,{7,8,9})->at(0)==std::vector<int>({7,8,9}));assert(fill_spiral_from_values(3,1,{1,2,3})->at(2).at(0)==3);return 0;}""",
        ("value count is exact", "zero dimensions require empty values", "matrix dimensions are exact", "degenerate rows and columns work", "every value is consumed once"),
        "shrinking-boundary spiral write with exact cardinality precheck", ("matrix-fill", "applied-file", "rectangular"),
    )
    add(
        "Spiral Matrix", "complete-spiral-path-validator", "Complete spiral path validator",
        "Validate that a coordinate sequence is exactly the clockwise top-left spiral for the declared rectangle. Coordinates must be in bounds, unique, and complete. Zero dimensions require an empty sequence. This function returns false rather than throwing for malformed paths.",
        "", "bool validates_clockwise_spiral(std::size_t rows, std::size_t columns, const std::vector<std::pair<std::size_t,std::size_t>>& path)",
        """bool charm::v1n3::spiral_matrix::validates_clockwise_spiral(std::size_t rows,std::size_t columns,const std::vector<std::pair<std::size_t,std::size_t>>& path){if(rows!=0&&columns>std::numeric_limits<std::size_t>::max()/rows)return false;if(path.size()!=rows*columns)return false;if(path.empty())return true;std::vector<std::vector<bool>> seen(rows,std::vector<bool>(columns));std::array<int,4> dr{0,1,0,-1},dc{1,0,-1,0};std::size_t r=0,c=0;int direction=0;for(const auto& point:path){if(point.first!=r||point.second!=c||seen[r][c])return false;seen[r][c]=true;long long nr=static_cast<long long>(r)+dr[direction],nc=static_cast<long long>(c)+dc[direction];if(nr<0||nc<0||nr>=static_cast<long long>(rows)||nc>=static_cast<long long>(columns)||seen[static_cast<std::size_t>(nr)][static_cast<std::size_t>(nc)]){direction=(direction+1)%4;nr=static_cast<long long>(r)+dr[direction];nc=static_cast<long long>(c)+dc[direction];}r=static_cast<std::size_t>(nr);c=static_cast<std::size_t>(nc);}return true;}""",
        """using charm::v1n3::spiral_matrix::validates_clockwise_spiral;
int main(){assert(validates_clockwise_spiral(2,2,{{0,0},{0,1},{1,1},{1,0}}));assert(validates_clockwise_spiral(0,5,{}));assert(!validates_clockwise_spiral(1,2,{{0,0}}));assert(!validates_clockwise_spiral(2,2,{{0,0},{1,0},{1,1},{0,1}}));assert(!validates_clockwise_spiral(1,1,{{1,0}}));return 0;}""",
        ("path cardinality is exact", "zero shapes are empty", "coordinates are in bounds", "order is not merely adjacency", "duplicates reject"),
        "online equality against a deterministic spiral state machine", ("validator", "completion", "path-order"),
    )

    # Sublist: exact relation names, wildcard windows, and repeated-pattern coverage.
    add(
        "Sublist", "explicit-contiguous-relation", "Explicit contiguous relation",
        "Classify two integer sequences using the exact SequenceRelation enumerators. containment means contiguous occurrence. Equal sequences are equal; otherwise a contained first sequence is proper_sublist, a containing first sequence is proper_superlist, and neither is unrelated. Empty-sequence behavior follows these definitions. Complexity is O(n*m) or better.",
        "enum class SequenceRelation { equal, proper_sublist, proper_superlist, unrelated };", "SequenceRelation classify_contiguous_relation(const std::vector<int>& first, const std::vector<int>& second)",
        """charm::v1n3::sublist::SequenceRelation charm::v1n3::sublist::classify_contiguous_relation(const std::vector<int>& first,const std::vector<int>& second){if(first==second)return SequenceRelation::equal;auto contains=[](const std::vector<int>& haystack,const std::vector<int>& needle){return std::search(haystack.begin(),haystack.end(),needle.begin(),needle.end())!=haystack.end();};if(contains(second,first))return SequenceRelation::proper_sublist;if(contains(first,second))return SequenceRelation::proper_superlist;return SequenceRelation::unrelated;}""",
        """using namespace charm::v1n3::sublist;
int main(){assert(classify_contiguous_relation({1,2},{0,1,2,3})==SequenceRelation::proper_sublist);assert(classify_contiguous_relation({1,2},{1,2})==SequenceRelation::equal);assert(classify_contiguous_relation({1,2},{2,1})==SequenceRelation::unrelated);assert(classify_contiguous_relation({}, {1})==SequenceRelation::proper_sublist);assert(classify_contiguous_relation({1}, {})==SequenceRelation::proper_superlist);return 0;}""",
        ("relation names are exact", "containment is contiguous", "equal precedes proper relations", "empty behavior is explicit", "repeated values use sequence equality"),
        "exact equality followed by directional contiguous searches", ("relation-enum", "generic-values", "complexity-bound"),
    )
    add(
        "Sublist", "optional-wildcard-windows", "Optional wildcard windows",
        "Return every start where a pattern of optional integers matches a contiguous window: an engaged optional requires equality and an empty optional matches any single value. An empty pattern matches every boundary. Overlapping matches are retained in ascending order.",
        "", "std::vector<std::size_t> optional_pattern_positions(const std::vector<int>& values, const std::vector<std::optional<int>>& pattern)",
        """std::vector<std::size_t> charm::v1n3::sublist::optional_pattern_positions(const std::vector<int>& values,const std::vector<std::optional<int>>& pattern){std::vector<std::size_t> out;if(pattern.empty()){for(std::size_t i=0;i<=values.size();++i)out.push_back(i);return out;}if(pattern.size()>values.size())return out;for(std::size_t start=0;start+pattern.size()<=values.size();++start){bool match=true;for(std::size_t i=0;i<pattern.size();++i)if(pattern[i]&&*pattern[i]!=values[start+i]){match=false;break;}if(match)out.push_back(start);}return out;}""",
        """using charm::v1n3::sublist::optional_pattern_positions;
int main(){using O=std::optional<int>;assert((optional_pattern_positions({1,2,1,3},{O{1},O{}})==std::vector<std::size_t>{0,2}));assert(optional_pattern_positions({1},{}).size()==2);assert(optional_pattern_positions({}, {O{}}).empty());assert(optional_pattern_positions({1,1},{O{1}})==(std::vector<std::size_t>{0,1}));assert(optional_pattern_positions({1,2},{O{2}})==std::vector<std::size_t>{1});return 0;}""",
        ("wildcard consumes exactly one value", "empty pattern matches boundaries", "overlaps remain", "long patterns have no match", "positions are ascending"),
        "bounded nested window comparison with explicit wildcard branches", ("wildcard", "window", "repeated-pattern"),
    )
    add(
        "Sublist", "minimum-covering-slice", "Minimum covering slice",
        "Find the shortest contiguous slice of values whose multiplicities cover every required value multiplicity. Return its half-open [begin,end) indices; ties choose the smaller begin. Empty requirements return [0,0]. If no slice covers the requirements return an empty optional.",
        "", "std::optional<std::pair<std::size_t,std::size_t>> minimum_covering_slice(const std::vector<int>& values, const std::vector<int>& required)",
        """std::optional<std::pair<std::size_t,std::size_t>> charm::v1n3::sublist::minimum_covering_slice(const std::vector<int>& values,const std::vector<int>& required){if(required.empty())return std::pair<std::size_t,std::size_t>{0,0};std::map<int,int> need,have;for(int value:required)++need[value];std::size_t satisfied=0,left=0,best_begin=0,best_end=0;bool found=false;for(std::size_t right=0;right<values.size();++right){int value=values[right];if(need.count(value)&&++have[value]==need[value])++satisfied;while(satisfied==need.size()){if(!found||right+1-left<best_end-best_begin){found=true;best_begin=left;best_end=right+1;}int drop=values[left++];if(need.count(drop)&&have[drop]--==need[drop])--satisfied;}}if(!found)return std::nullopt;return std::pair<std::size_t,std::size_t>{best_begin,best_end};}""",
        """using charm::v1n3::sublist::minimum_covering_slice;
int main(){assert((minimum_covering_slice({1,2,1,3,2},{1,2,2})==std::pair<std::size_t,std::size_t>(1,5)));assert((minimum_covering_slice({1,2},{})==std::pair<std::size_t,std::size_t>(0,0)));assert(!minimum_covering_slice({1},{1,1}));assert((minimum_covering_slice({2,1,2,1},{1,2})==std::pair<std::size_t,std::size_t>(0,2)));assert(!minimum_covering_slice({}, {1}));return 0;}""",
        ("multiplicity matters", "result is half-open", "ties use smaller begin", "empty requirement is zero slice", "missing coverage is empty optional"),
        "multiplicity-satisfied sliding window with deterministic contraction", ("covering-window", "multiplicity", "linear"),
    )

    # Yacht: string category representation, exhaustive dice validation, and deterministic sheets.
    add(
        "Yacht", "string-rule-score", "String rule score",
        "Score exactly five six-sided dice under a string rule. Supported case-sensitive rules are sum, all-even, three-match, and full-run. sum totals all dice; all-even scores the sum only if every die is even; three-match scores the sum when any face occurs at least three times; full-run scores 30 for 1-5 or 2-6. Unknown rules or invalid dice reject.",
        "", "std::optional<int> score_string_rule(std::string_view rule, const std::array<int,5>& dice)",
        """std::optional<int> charm::v1n3::yacht::score_string_rule(std::string_view rule,const std::array<int,5>& dice){std::array<int,7> counts{};int sum=0;for(int die:dice){if(die<1||die>6)return std::nullopt;++counts[die];sum+=die;}if(rule=="sum")return sum;if(rule=="all-even")return std::all_of(dice.begin(),dice.end(),[](int d){return d%2==0;})?sum:0;if(rule=="three-match")return *std::max_element(counts.begin(),counts.end())>=3?sum:0;if(rule=="full-run"){std::set<int> faces(dice.begin(),dice.end());return faces==std::set<int>({1,2,3,4,5})||faces==std::set<int>({2,3,4,5,6})?30:0;}return std::nullopt;}""",
        """using charm::v1n3::yacht::score_string_rule;
int main(){assert(score_string_rule("sum",{1,2,3,4,5})==15);assert(score_string_rule("all-even",{2,2,4,4,6})==18);assert(score_string_rule("three-match",{3,3,3,1,2})==12);assert(score_string_rule("full-run",{6,2,5,3,4})==30);assert(!score_string_rule("yacht",{1,1,1,1,1}));assert(!score_string_rule("sum",{0,1,2,3,4}));return 0;}""",
        ("category representation is string", "rules are case-sensitive", "unknown rules reject", "all dice are validated", "rule boundaries are exhaustive"),
        "validated face histogram with explicit string-dispatched scoring", ("string-category", "exhaustive", "direct-include"),
    )
    add(
        "Yacht", "best-declared-rule", "Best declared rule",
        "Choose the highest-scoring rule from a declared nonempty list using the same four rule names as score_string_rule. Rule names must be unique and valid; ties choose the lexically smaller rule. Return the chosen rule and score after validating all five dice.",
        "", "std::optional<std::pair<std::string,int>> best_declared_rule(const std::array<int,5>& dice, const std::vector<std::string>& rules)",
        """std::optional<std::pair<std::string,int>> charm::v1n3::yacht::best_declared_rule(const std::array<int,5>& dice,const std::vector<std::string>& rules){if(rules.empty())return std::nullopt;auto score_rule=[&](const std::string& rule)->std::optional<int>{std::array<int,7> counts{};int sum=0;for(int die:dice){if(die<1||die>6)return std::nullopt;++counts[die];sum+=die;}if(rule=="sum")return sum;if(rule=="all-even")return std::all_of(dice.begin(),dice.end(),[](int d){return d%2==0;})?sum:0;if(rule=="three-match")return *std::max_element(counts.begin(),counts.end())>=3?sum:0;if(rule=="full-run"){std::set<int> faces(dice.begin(),dice.end());return faces==std::set<int>({1,2,3,4,5})||faces==std::set<int>({2,3,4,5,6})?30:0;}return std::nullopt;};std::set<std::string> seen;std::optional<std::pair<std::string,int>> best;for(const auto& rule:rules){if(!seen.insert(rule).second)return std::nullopt;auto score=score_rule(rule);if(!score)return std::nullopt;if(!best||*score>best->second||(*score==best->second&&rule<best->first))best=std::pair<std::string,int>{rule,*score};}return best;}""",
        """using charm::v1n3::yacht::best_declared_rule;
int main(){auto r=best_declared_rule({1,2,3,4,5},{"sum","full-run"});assert(r&&r->first=="full-run"&&r->second==30);assert(best_declared_rule({1,1,2,2,3},{"sum","three-match"})->first=="sum");assert(!best_declared_rule({1,2,3,4,5},{}));assert(!best_declared_rule({1,2,3,4,5},{"sum","sum"}));assert(!best_declared_rule({1,2,3,4,5},{"unknown"}));return 0;}""",
        ("rule list is nonempty", "rules are unique", "unknown rules reject", "higher score wins", "ties are lexical"),
        "validated rule-set enumeration with score then lexical comparison", ("selection", "string-category", "tie-break"),
    )
    add(
        "Yacht", "unique-score-sheet", "Unique score sheet",
        "Score a sheet of named turns. Each row supplies one of the four supported string rules and five dice; a rule may appear at most once. Invalid rows reject the entire sheet. Return total score, number of used rules, and count of zero-scoring rows.",
        "struct YachtTurn { std::string rule; std::array<int,5> dice; };", "std::optional<std::array<int,3>> summarize_unique_score_sheet(const std::vector<YachtTurn>& turns)",
        """std::optional<std::array<int,3>> charm::v1n3::yacht::summarize_unique_score_sheet(const std::vector<charm::v1n3::yacht::YachtTurn>& turns){auto score_rule=[](const YachtTurn& turn)->std::optional<int>{std::array<int,7> counts{};int sum=0;for(int die:turn.dice){if(die<1||die>6)return std::nullopt;++counts[die];sum+=die;}if(turn.rule=="sum")return sum;if(turn.rule=="all-even")return std::all_of(turn.dice.begin(),turn.dice.end(),[](int d){return d%2==0;})?sum:0;if(turn.rule=="three-match")return *std::max_element(counts.begin(),counts.end())>=3?sum:0;if(turn.rule=="full-run"){std::set<int> faces(turn.dice.begin(),turn.dice.end());return faces==std::set<int>({1,2,3,4,5})||faces==std::set<int>({2,3,4,5,6})?30:0;}return std::nullopt;};std::set<std::string> rules;int total=0,zeros=0;for(const auto& turn:turns){if(!rules.insert(turn.rule).second)return std::nullopt;auto score=score_rule(turn);if(!score||total>std::numeric_limits<int>::max()-*score)return std::nullopt;total+=*score;if(*score==0)++zeros;}return std::array<int,3>{total,static_cast<int>(rules.size()),zeros};}""",
        """using namespace charm::v1n3::yacht;
int main(){auto r=summarize_unique_score_sheet({{"sum",{1,1,1,1,1}},{"all-even",{1,2,2,2,2}}});assert(r&&*r==(std::array<int,3>{5,2,1}));assert(summarize_unique_score_sheet({})->at(0)==0);assert(!summarize_unique_score_sheet({{"sum",{1,1,1,1,1}},{"sum",{2,2,2,2,2}}}));assert(!summarize_unique_score_sheet({{"bad",{1,1,1,1,1}}}));assert(!summarize_unique_score_sheet({{"sum",{7,1,1,1,1}}}));return 0;}""",
        ("each rule is used once", "unknown categories reject", "invalid dice reject", "zero scores are counted", "empty sheet summarizes to zeros"),
        "identity-checked sheet fold through the shared exhaustive scorer", ("score-sheet", "unique-category", "boundaries"),
    )

    # Zebra Puzzle: explicit bounded solve entry points and deterministic validation.
    add(
        "Zebra Puzzle", "fixed-position-house-solver", "Fixed position house solver",
        "Use the exact solve_house_assignment entry point and HouseAssignment result type. Assign each distinct nonempty item to one of house_count positions. Fixed clues name an item and position; unclued items fill remaining positions lexically. Reject contradictions, unknown items, duplicate item names, invalid positions, or house_count above 10.",
        "struct FixedHouseClue { std::string item; std::size_t position; }; struct HouseAssignment { std::vector<std::string> item_at_position; };", "std::optional<HouseAssignment> solve_house_assignment(std::size_t house_count, const std::vector<std::string>& items, const std::vector<FixedHouseClue>& clues)",
        """std::optional<charm::v1n3::zebra_puzzle::HouseAssignment> charm::v1n3::zebra_puzzle::solve_house_assignment(std::size_t house_count,const std::vector<std::string>& items,const std::vector<charm::v1n3::zebra_puzzle::FixedHouseClue>& clues){if(house_count>10||items.size()!=house_count)return std::nullopt;std::set<std::string> domain;for(const auto& item:items)if(item.empty()||!domain.insert(item).second)return std::nullopt;std::vector<std::string> positions(house_count);std::set<std::string> fixed;for(const auto& clue:clues){if(clue.position>=house_count||domain.count(clue.item)==0||!fixed.insert(clue.item).second||!positions[clue.position].empty())return std::nullopt;positions[clue.position]=clue.item;}std::vector<std::string> remaining;for(const auto& item:domain)if(fixed.count(item)==0)remaining.push_back(item);auto it=remaining.begin();for(auto& position:positions)if(position.empty())position=*it++;return HouseAssignment{positions};}""",
        """using namespace charm::v1n3::zebra_puzzle;
int main(){auto r=solve_house_assignment(3,{"zebra","water","coffee"},{{"water",1}});assert(r&&r->item_at_position==(std::vector<std::string>{"coffee","water","zebra"}));assert(solve_house_assignment(0,{},{})->item_at_position.empty());assert(!solve_house_assignment(2,{"a"},{}));assert(!solve_house_assignment(2,{"a","a"},{}));assert(!solve_house_assignment(2,{"a","b"},{{"x",0}}));return 0;}""",
        ("solve entry point is exact", "result type is explicit", "domain size equals houses", "clues are noncontradictory", "unclued fill is lexical and bounded"),
        "fixed-slot constraint application followed by lexical completion", ("solve-api", "bounded", "deterministic"),
    )
    add(
        "Zebra Puzzle", "ordered-adjacency-permutation-solver", "Ordered adjacency permutation solver",
        "Solve a permutation of distinct labels subject to before and adjacent constraints. Return the lexically smallest satisfying left-to-right order. All labels and constraint endpoints must exist, labels are limited to eight, and self-constraints reject. Return an empty inner optional when a valid problem has no solution.",
        "struct OrderClue { std::string before; std::string after; }; struct AdjacentClue { std::string first; std::string second; };", "std::optional<std::optional<std::vector<std::string>>> solve_ordered_adjacency(const std::vector<std::string>& labels, const std::vector<OrderClue>& orders, const std::vector<AdjacentClue>& adjacent)",
        """std::optional<std::optional<std::vector<std::string>>> charm::v1n3::zebra_puzzle::solve_ordered_adjacency(const std::vector<std::string>& labels,const std::vector<charm::v1n3::zebra_puzzle::OrderClue>& orders,const std::vector<charm::v1n3::zebra_puzzle::AdjacentClue>& adjacent){if(labels.size()>8)return std::nullopt;std::set<std::string> domain(labels.begin(),labels.end());if(domain.size()!=labels.size()||domain.count("")!=0)return std::nullopt;auto known=[&](const std::string& a,const std::string& b){return a!=b&&domain.count(a)&&domain.count(b);};for(const auto& c:orders)if(!known(c.before,c.after))return std::nullopt;for(const auto& c:adjacent)if(!known(c.first,c.second))return std::nullopt;std::vector<std::string> candidate(domain.begin(),domain.end());do{std::map<std::string,std::size_t> pos;for(std::size_t i=0;i<candidate.size();++i)pos[candidate[i]]=i;bool ok=true;for(const auto& c:orders)ok=ok&&pos[c.before]<pos[c.after];for(const auto& c:adjacent)ok=ok&&(pos[c.first]+1==pos[c.second]||pos[c.second]+1==pos[c.first]);if(ok)return std::optional<std::vector<std::string>>{candidate};}while(std::next_permutation(candidate.begin(),candidate.end()));return std::optional<std::vector<std::string>>{};}""",
        """using namespace charm::v1n3::zebra_puzzle;
int main(){auto r=solve_ordered_adjacency({"c","a","b"},{{"a","c"}},{{"b","c"}});assert(r&&*r&&**r==(std::vector<std::string>{"a","b","c"}));auto none=solve_ordered_adjacency({"a","b"},{{"a","b"},{"b","a"}},{});assert(none&&!*none);assert(!solve_ordered_adjacency({"a","a"},{},{}));assert(!solve_ordered_adjacency({"a"},{{"a","x"}},{}));assert(solve_ordered_adjacency({}, {}, {})->value().empty());return 0;}""",
        ("outer optional validates problem", "inner optional reports satisfiability", "lexically smallest solution wins", "label count is bounded", "constraints use known distinct labels"),
        "bounded lexical permutation enumeration with positional constraint checks", ("constraint-solver", "permutation", "completion"),
    )
    add(
        "Zebra Puzzle", "complete-house-solution-validator", "Complete house solution validator",
        "Validate a completed assignment of named attributes to houses. Every row must contain exactly attribute_count distinct nonempty values, and every value must appear in exactly one house globally. Equality clues require two values in the same house; neighbor clues require houses whose indices differ by one. Unknown clue values reject.",
        "struct ValuePairClue { std::string first; std::string second; };", "bool validate_complete_house_solution(const std::vector<std::vector<std::string>>& houses, std::size_t attribute_count, const std::vector<ValuePairClue>& equal_house, const std::vector<ValuePairClue>& neighbors)",
        """bool charm::v1n3::zebra_puzzle::validate_complete_house_solution(const std::vector<std::vector<std::string>>& houses,std::size_t attribute_count,const std::vector<charm::v1n3::zebra_puzzle::ValuePairClue>& equal_house,const std::vector<charm::v1n3::zebra_puzzle::ValuePairClue>& neighbors){std::map<std::string,std::size_t> location;for(std::size_t h=0;h<houses.size();++h){if(houses[h].size()!=attribute_count)return false;std::set<std::string> row;for(const auto& value:houses[h])if(value.empty()||!row.insert(value).second||!location.emplace(value,h).second)return false;}auto known=[&](const ValuePairClue& c){return location.count(c.first)&&location.count(c.second)&&c.first!=c.second;};for(const auto& c:equal_house)if(!known(c)||location[c.first]!=location[c.second])return false;for(const auto& c:neighbors)if(!known(c)||std::llabs(static_cast<long long>(location[c.first])-static_cast<long long>(location[c.second]))!=1)return false;return true;}""",
        """using namespace charm::v1n3::zebra_puzzle;
int main(){assert(validate_complete_house_solution({{"red","tea"},{"blue","water"}},2,{{"red","tea"}},{{"tea","water"}}));assert(validate_complete_house_solution({},0,{},{}));assert(!validate_complete_house_solution({{"a","a"}},2,{},{}));assert(!validate_complete_house_solution({{"a"},{"a"}},1,{},{}));assert(!validate_complete_house_solution({{"a"}},1,{{"a","x"}},{}));return 0;}""",
        ("row width is exact", "values are globally unique", "clues use known distinct values", "equality uses same house", "neighbor distance is exactly one"),
        "global value-location index with exhaustive clue verification", ("solution-validator", "result-completion", "bounded-output"),
    )

    return specs
