"""Fresh clean-room CHARM V1 specifications for the r87 rematerialization."""

from __future__ import annotations

import re
from typing import Any


NAMESPACE_BATCH = "v1r87_37414"


def _line_break_cpp_statements(source: str) -> str:
    """Put semicolon-terminated statements on deterministic physical lines."""
    output: list[str] = []
    parenthesis_depth = 0
    quote = ""
    escaped = False
    for character in source:
        output.append(character)
        if quote:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = ""
            continue
        if character in {'"', "'"}:
            quote = character
        elif character == "(":
            parenthesis_depth += 1
        elif character == ")":
            parenthesis_depth -= 1
            if parenthesis_depth < 0:
                raise ValueError("unbalanced C++ body parentheses")
        elif character == "}" and parenthesis_depth == 0:
            output.append("\n")
        elif character == ";" and parenthesis_depth == 0:
            output.append("\n")
    if quote or parenthesis_depth:
        raise ValueError("unterminated C++ body quote or parentheses")
    return "".join(output)


def build_specs(spec_type: type[Any]) -> list[Any]:
    specs: list[Any] = []

    def add(
        topic: str,
        slug: str,
        title: str,
        contract: str,
        types: str,
        signature: str,
        body: str,
        tests: str,
        edges: tuple[str, ...],
        strategy: str,
        tags: tuple[str, ...],
    ) -> None:
        topic_ns = re.sub(r"[^a-z0-9]+", "_", topic.casefold()).strip("_")
        namespace = f"charm::{NAMESPACE_BATCH}::{topic_ns}"
        formatted_body = _line_break_cpp_statements(body.strip())
        definition = f"namespace {namespace} {{\n{signature} {{\n{formatted_body}\n}}\n}}"
        tests_source = f"using namespace {namespace};\nint main() {{\n{tests.strip()}\nreturn 0;\n}}"
        specs.append(
            spec_type(
                topic,
                slug,
                title,
                contract,
                types,
                signature,
                definition,
                tests_source,
                edges,
                strategy,
                tags,
            )
        )

    # Allergies: boolean label rules, decontamination coverage, and rotation audits.
    add(
        "Allergies", "allergen-rule-evaluator", "Allergen rule evaluator",
        "Evaluate a fully parenthesized boolean rule over allergen labels. Leaves are nonempty lowercase identifiers; operators are !, &, and |. Whitespace is ignored and malformed syntax rejects.",
        "", "std::optional<bool> evaluate_allergen_rule(std::string_view expression, const std::set<std::string>& present)",
        r'''
std::size_t pos=0; auto skip=[&]{while(pos<expression.size()&&std::isspace(static_cast<unsigned char>(expression[pos])))++pos;};
std::function<std::optional<bool>()> parse=[&]() -> std::optional<bool>{skip();if(pos>=expression.size())return std::nullopt;if(expression[pos]=='!'){++pos;auto v=parse();return v?std::optional<bool>{!*v}:std::nullopt;}if(expression[pos]=='('){++pos;auto a=parse();skip();if(!a||pos>=expression.size()||(expression[pos]!='&'&&expression[pos]!='|'))return std::nullopt;char op=expression[pos++];auto b=parse();skip();if(!b||pos>=expression.size()||expression[pos++]!=')')return std::nullopt;return op=='&'?*a&&*b:*a||*b;}std::size_t begin=pos;while(pos<expression.size()&&expression[pos]>='a'&&expression[pos]<='z')++pos;if(begin==pos)return std::nullopt;return present.count(std::string(expression.substr(begin,pos-begin)))!=0;};
auto result=parse();skip();if(!result||pos!=expression.size())return std::nullopt;return result;
''',
        r'''
require_case(evaluate_allergen_rule("(milk&!egg)",{"milk"})==true);
require_case(evaluate_allergen_rule(" (milk | egg) ",{"egg"})==true);
require_case(evaluate_allergen_rule("!milk",{})==true);
require_case(!evaluate_allergen_rule("milk&egg",{"milk"}));
require_case(!evaluate_allergen_rule("Milk",{}));
''',
        ("identifiers are lowercase ASCII", "binary operators require parentheses", "negation binds one expression", "trailing input rejects", "membership is exact"),
        "recursive-descent evaluation of a deliberately small public grammar", ("parser", "boolean-rule", "public-grammar"),
    )
    add(
        "Allergies", "decontamination-cover", "Decontamination cover",
        "Choose the lexicographically earliest minimum-cardinality set of cleaning procedures whose bit masks cover every requested allergen bit. At most twenty procedures and twenty known bits are accepted.",
        "", "std::optional<std::vector<std::size_t>> minimum_cleaning_cover(const std::vector<std::uint32_t>& procedure_masks, std::uint32_t required_mask, std::uint32_t known_mask)",
        r'''
if((required_mask&~known_mask)!=0||procedure_masks.size()>20){return std::nullopt;}for(auto m:procedure_masks)if((m&~known_mask)!=0)return std::nullopt;
std::vector<std::size_t> best;bool found=false;const std::uint64_t limit=std::uint64_t{1}<<procedure_masks.size();for(std::uint64_t bits=0;bits<limit;++bits){std::uint32_t cover=0;std::vector<std::size_t> pick;for(std::size_t i=0;i<procedure_masks.size();++i)if(bits&(std::uint64_t{1}<<i)){cover|=procedure_masks[i];pick.push_back(i);}if((cover&required_mask)!=required_mask)continue;if(!found||pick.size()<best.size()||(pick.size()==best.size()&&pick<best)){best=pick;found=true;}}if(!found)return std::vector<std::size_t>{};return best;
''',
        r'''
require_case(minimum_cleaning_cover({1,2,3},3,3).value()==std::vector<std::size_t>{2});
require_case(minimum_cleaning_cover({1,2},3,3).value()==(std::vector<std::size_t>{0,1}));
require_case(minimum_cleaning_cover({},0,7).value().empty());
require_case(minimum_cleaning_cover({},1,1).value().empty());
require_case(!minimum_cleaning_cover({8},1,3));
''',
        ("unknown bits reject", "empty requirement needs no procedure", "impossible cover has an empty inner result", "minimum cardinality dominates", "ties use index-vector order"),
        "bounded subset enumeration with canonical witness selection", ("set-cover", "bit-domain", "witness"),
    )
    add(
        "Allergies", "exposure-rotation-audit", "Exposure rotation audit",
        "Audit a day-indexed allergen rotation. Each record names one allergen and a nonnegative day; records are strictly day-ordered. Return every adjacent same-allergen pair closer than its declared cooldown, preserving encounter order.",
        "struct RotationEntry { int day; std::string allergen; };", "std::optional<std::vector<std::pair<std::size_t,std::size_t>>> audit_exposure_rotation(const std::vector<RotationEntry>& entries, const std::map<std::string,int>& cooldown_days)",
        r'''
std::map<std::string,std::pair<int,std::size_t>> last;std::vector<std::pair<std::size_t,std::size_t>> out;int prior=-1;for(std::size_t i=0;i<entries.size();++i){const auto&e=entries[i];auto c=cooldown_days.find(e.allergen);if(e.day<0||e.day<=prior||e.allergen.empty()||c==cooldown_days.end()||c->second<0)return std::nullopt;auto p=last.find(e.allergen);if(p!=last.end()&&static_cast<long long>(e.day)-p->second.first<c->second)out.push_back({p->second.second,i});last[e.allergen]={e.day,i};prior=e.day;}return out;
''',
        r'''
require_case(audit_exposure_rotation({{1,"a"},{3,"b"},{4,"a"}},{{"a",5},{"b",0}}).value()==(std::vector<std::pair<std::size_t,std::size_t>>{{0,2}}));
require_case(audit_exposure_rotation({},{}).value().empty());
require_case(!audit_exposure_rotation({{1,"x"}},{}));
require_case(!audit_exposure_rotation({{2,"a"},{2,"a"}},{{"a",1}}));
require_case(audit_exposure_rotation({{1,"a"},{6,"a"}},{{"a",5}}).value().empty());
''',
        ("days are strictly increasing", "all labels have cooldowns", "cooldowns are nonnegative", "the cooldown boundary is allowed", "only consecutive occurrences of one label pair"),
        "last-occurrence state keyed by allergen", ("rotation", "cooldown", "audit"),
    )

    # Bank Account: escrow replay, exact conversion cycles, and business-day orders.
    add(
        "Bank Account", "escrow-tranche-replay", "Escrow tranche replay",
        "Replay account-scoped escrow deposits and releases. Amounts must be positive, a release may not exceed its account balance, and the result lists nonzero balances by account.",
        "struct EscrowEvent { std::string account; std::int64_t amount; bool release; };", "std::optional<std::map<std::string,std::int64_t>> replay_escrow_tranches(const std::vector<EscrowEvent>& events)",
        r'''
std::map<std::string,std::int64_t> balances;for(const auto&e:events){if(e.account.empty()||e.amount<=0)return std::nullopt;auto&v=balances[e.account];if(e.release){if(v<e.amount)return std::nullopt;v-=e.amount;}else{if(v>std::numeric_limits<std::int64_t>::max()-e.amount)return std::nullopt;v+=e.amount;}}for(auto it=balances.begin();it!=balances.end();)if(it->second==0)it=balances.erase(it);else ++it;return balances;
''',
        r'''
require_case(replay_escrow_tranches({{"a",7,false},{"a",2,true}}).value()==std::map<std::string,std::int64_t>{{"a",5}});
require_case(replay_escrow_tranches({{"a",3,false},{"a",3,true}}).value().empty());
require_case(!replay_escrow_tranches({{"a",1,true}}));
require_case(!replay_escrow_tranches({{"",1,false}}));
require_case(!replay_escrow_tranches({{"a",0,false}}));
''',
        ("amounts are strictly positive", "accounts are nonempty", "releases never overdraw", "overflow rejects", "zero final balances are omitted"),
        "checked ledger replay keyed by account", ("ledger", "escrow", "overflow"),
    )
    add(
        "Bank Account", "closed-conversion-cycle", "Closed conversion cycle",
        "Apply an ordered currency cycle of exact positive rational rates. Every intermediate numerator product must fit int64 and divide exactly; report whether the final amount equals the initial positive amount.",
        "", "std::optional<bool> closes_exact_conversion_cycle(std::int64_t amount, const std::vector<std::pair<std::int64_t,std::int64_t>>& rates)",
        r'''
if(amount<=0)return std::nullopt;std::int64_t value=amount;for(auto [n,d]:rates){if(n<=0||d<=0)return std::nullopt;if(value>std::numeric_limits<std::int64_t>::max()/n)return std::nullopt;auto product=value*n;if(product%d!=0)return std::nullopt;value=product/d;}return value==amount;
''',
        r'''
require_case(closes_exact_conversion_cycle(10,{{3,2},{2,3}})==true);
require_case(closes_exact_conversion_cycle(10,{{2,1}})==false);
require_case(!closes_exact_conversion_cycle(5,{{1,2}}));
require_case(!closes_exact_conversion_cycle(0,{}));
require_case(!closes_exact_conversion_cycle(2,{{0,1}}));
''',
        ("the opening amount is positive", "rates have positive terms", "every step is integral", "overflow rejects", "an empty cycle closes"),
        "checked exact rational replay without floating point", ("currency", "rational", "cycle"),
    )
    add(
        "Bank Account", "standing-order-calendar", "Standing order calendar",
        "Move requested nonnegative day indices forward to the next business day. Day zero has a supplied weekday in [0,6], weekdays 5 and 6 are weekends, holidays are nonnegative, and equal settled days aggregate amounts.",
        "struct StandingOrder { int requested_day; std::int64_t amount; };", "std::optional<std::map<int,std::int64_t>> settle_standing_orders(const std::vector<StandingOrder>& orders, int weekday_of_day_zero, const std::set<int>& holidays)",
        r'''
if(weekday_of_day_zero<0||weekday_of_day_zero>6)return std::nullopt;for(int h:holidays)if(h<0)return std::nullopt;std::map<int,std::int64_t> out;for(const auto&o:orders){if(o.requested_day<0||o.amount<=0)return std::nullopt;int d=o.requested_day;while(((weekday_of_day_zero+d)%7)>=5||holidays.count(d)){if(d==std::numeric_limits<int>::max())return std::nullopt;++d;}auto&v=out[d];if(v>std::numeric_limits<std::int64_t>::max()-o.amount)return std::nullopt;v+=o.amount;}return out;
''',
        r'''
require_case(settle_standing_orders({{5,2},{6,3}},0,{}).value()==std::map<int,std::int64_t>{{7,5}});
require_case(settle_standing_orders({{0,4}},0,{0,1}).value()==std::map<int,std::int64_t>{{2,4}});
require_case(settle_standing_orders({},6,{}).value().empty());
require_case(!settle_standing_orders({{-1,2}},0,{}));
require_case(!settle_standing_orders({},7,{}));
''',
        ("day indices and holidays are nonnegative", "weekday is in range", "amounts are positive", "weekends and holidays shift forward", "settled collisions aggregate with overflow checks"),
        "calendar normalization followed by checked aggregation", ("calendar", "business-day", "aggregation"),
    )

    # Binary Search Tree: traversal reconstruction and structural certificates.
    add(
        "Binary Search Tree", "traversal-parent-reconstruction", "Traversal parent reconstruction",
        "Given preorder and inorder traversals of the same distinct integer keys, reconstruct each preorder element's parent preorder index. The root parent is -1; inconsistent traversals reject.",
        "", "std::optional<std::vector<int>> reconstruct_preorder_parents(const std::vector<int>& preorder, const std::vector<int>& inorder)",
        r'''
if(preorder.size()!=inorder.size())return std::nullopt;std::map<int,int> at;for(std::size_t i=0;i<inorder.size();++i)if(!at.emplace(inorder[i],static_cast<int>(i)).second)return std::nullopt;std::set<int> seen;std::vector<int> parent(preorder.size(),-2);std::size_t p=0;std::function<bool(int,int,int)> rec=[&](int lo,int hi,int par){if(lo>=hi)return true;if(p>=preorder.size()||!seen.insert(preorder[p]).second)return false;auto it=at.find(preorder[p]);if(it==at.end()||it->second<lo||it->second>=hi)return false;int root=it->second;int me=static_cast<int>(p);parent[p++]=par;return rec(lo,root,me)&&rec(root+1,hi,me);};if(!rec(0,static_cast<int>(inorder.size()),-1)||p!=preorder.size())return std::nullopt;return parent;
''',
        r'''
require_case(reconstruct_preorder_parents({4,2,1,3,6},{1,2,3,4,6}).value()==std::vector<int>({-1,0,1,1,0}));
require_case(reconstruct_preorder_parents({},{}).value().empty());
require_case(!reconstruct_preorder_parents({1,1},{1,1}));
require_case(!reconstruct_preorder_parents({1,2},{2,3}));
require_case(!reconstruct_preorder_parents({1,2},{1}));
''',
        ("traversal sizes match", "keys are distinct", "sets and recursive partitions agree", "empty input is valid", "parents index preorder positions"),
        "recursive inorder interval reconstruction", ("bst", "traversal", "reconstruction"),
    )
    add(
        "Binary Search Tree", "avl-certificate-audit", "AVL certificate audit",
        "Audit array-indexed nodes as one strict BST and AVL tree rooted at the supplied index. Child index -1 means absent. Reject cycles, shared children, unreachable nodes, duplicate keys, or balance magnitude above one; return computed root height.",
        "struct AvlNode { int key; int left; int right; };", "std::optional<int> audit_avl_certificate(const std::vector<AvlNode>& nodes, int root)",
        r'''
if(nodes.empty())return root==-1?std::optional<int>{0}:std::nullopt;if(root<0||root>=static_cast<int>(nodes.size()))return std::nullopt;std::vector<int> state(nodes.size());std::function<std::optional<int>(int,std::optional<int>,std::optional<int>)> dfs=[&](int i,std::optional<int>lo,std::optional<int>hi)->std::optional<int>{if(i==-1)return 0;if(i<0||i>=static_cast<int>(nodes.size())||state[i])return std::nullopt;const auto&n=nodes[i];if((lo&&n.key<=*lo)||(hi&&n.key>=*hi))return std::nullopt;state[i]=1;auto a=dfs(n.left,lo,n.key),b=dfs(n.right,n.key,hi);if(!a||!b||std::abs(*a-*b)>1)return std::nullopt;state[i]=2;return 1+std::max(*a,*b);};auto h=dfs(root,std::nullopt,std::nullopt);if(!h||std::any_of(state.begin(),state.end(),[](int x){return x!=2;}))return std::nullopt;return h;
''',
        r'''
require_case(audit_avl_certificate({{2,1,2},{1,-1,-1},{3,-1,-1}},0)==2);
require_case(audit_avl_certificate({},-1)==0);
require_case(!audit_avl_certificate({{2,1,-1},{1,2,-1},{0,-1,-1}},0));
require_case(!audit_avl_certificate({{2,1,1},{1,-1,-1}},0));
require_case(!audit_avl_certificate({{2,-1,-1},{1,-1,-1}},0));
''',
        ("-1 is the only null index", "all nodes are reachable exactly once", "ordering is strict", "balance is height-based", "empty tree requires root -1"),
        "bounded DFS with ownership, ordering, and height invariants", ("avl", "certificate", "graph-audit"),
    )
    add(
        "Binary Search Tree", "successor-thread-audit", "Successor thread audit",
        "For an array-indexed strict BST, audit each node's stored inorder-successor index. Return bad node indices in ascending order. Structural invalidity rejects before thread comparison.",
        "struct ThreadedNode { int key; int left; int right; int successor; };", "std::optional<std::vector<int>> audit_successor_threads(const std::vector<ThreadedNode>& nodes, int root)",
        r'''
if(nodes.empty())return root==-1?std::optional<std::vector<int>>{std::vector<int>{}}:std::nullopt;if(root<0||root>=static_cast<int>(nodes.size()))return std::nullopt;std::vector<int> seen(nodes.size()),order;std::function<bool(int,std::optional<int>,std::optional<int>)> dfs=[&](int i,std::optional<int>lo,std::optional<int>hi){if(i==-1)return true;if(i<0||i>=static_cast<int>(nodes.size())||seen[i])return false;const auto&n=nodes[i];if((lo&&n.key<=*lo)||(hi&&n.key>=*hi))return false;seen[i]=1;return dfs(n.left,lo,n.key)&&(order.push_back(i),true)&&dfs(n.right,n.key,hi);};if(!dfs(root,std::nullopt,std::nullopt)||std::any_of(seen.begin(),seen.end(),[](int x){return !x;}))return std::nullopt;std::vector<int> bad;for(std::size_t k=0;k<order.size();++k){int expected=k+1<order.size()?order[k+1]:-1;if(nodes[order[k]].successor!=expected)bad.push_back(order[k]);}std::sort(bad.begin(),bad.end());return bad;
''',
        r'''
require_case(audit_successor_threads({{2,1,2,2},{1,-1,-1,0},{3,-1,-1,-1}},0).value().empty());
require_case(audit_successor_threads({{2,1,2,-1},{1,-1,-1,0},{3,-1,-1,-1}},0).value()==std::vector<int>{0});
require_case(audit_successor_threads({},-1).value().empty());
require_case(!audit_successor_threads({{1,0,-1,-1}},0));
require_case(!audit_successor_threads({{2,-1,-1,-1},{1,-1,-1,-1}},0));
''',
        ("the BST must be one owned tree", "ordering is strict", "successor uses array indices", "the maximum expects -1", "bad indices are sorted"),
        "inorder derivation followed by independent thread comparison", ("threaded-tree", "successor", "audit"),
    )

    # Circular Buffer: versioned cursors, cyclic matching, and fair quota drains.
    add(
        "Circular Buffer", "cursor-snapshot-replay", "Cursor snapshot replay",
        "Replay a fixed-capacity integer ring with push-back, pop-front, save-cursor, and restore-cursor commands. Restore replaces the live ring with the named saved snapshot; malformed commands, unknown names, overflow, or underflow reject.",
        "struct RingCommand { std::string op; std::string name; int value; };", "std::optional<std::vector<int>> replay_ring_snapshots(std::size_t capacity, const std::vector<RingCommand>& commands)",
        r'''
std::deque<int> ring;std::map<std::string,std::deque<int>> saved;for(const auto&c:commands){if(c.op=="push"){if(!c.name.empty()||ring.size()==capacity)return std::nullopt;ring.push_back(c.value);}else if(c.op=="pop"){if(!c.name.empty()||ring.empty())return std::nullopt;ring.pop_front();}else if(c.op=="save"){if(c.name.empty()||saved.count(c.name))return std::nullopt;saved[c.name]=ring;}else if(c.op=="restore"){auto it=saved.find(c.name);if(c.name.empty()||it==saved.end())return std::nullopt;ring=it->second;}else return std::nullopt;}return std::vector<int>(ring.begin(),ring.end());
''',
        r'''
require_case(replay_ring_snapshots(3,{{"push","",1},{"save","a",0},{"push","",2},{"restore","a",0}}).value()==std::vector<int>{1});
require_case(replay_ring_snapshots(0,{}).value().empty());
require_case(!replay_ring_snapshots(1,{{"push","",1},{"push","",2}}));
require_case(!replay_ring_snapshots(2,{{"restore","x",0}}));
require_case(!replay_ring_snapshots(2,{{"save","x",0},{"save","x",0}}));
''',
        ("capacity zero permits only empty live rings", "snapshot names are nonempty and unique", "restore is non-destructive to the snapshot", "push/pop names are empty", "all invalid operations reject"),
        "deterministic deque state plus immutable named snapshots", ("ring", "snapshot", "command-replay"),
    )
    add(
        "Circular Buffer", "cyclic-hamming-starts", "Cyclic Hamming starts",
        "Return every start index in a nonempty circular text whose length-sized cyclic window differs from a nonempty pattern in at most the supplied mismatch budget. A pattern may wrap around the text multiple times.",
        "", "std::optional<std::vector<std::size_t>> cyclic_hamming_starts(std::string_view text, std::string_view pattern, std::size_t mismatch_budget)",
        r'''
if(text.empty()||pattern.empty())return std::nullopt;std::vector<std::size_t> out;for(std::size_t s=0;s<text.size();++s){std::size_t bad=0;for(std::size_t j=0;j<pattern.size()&&bad<=mismatch_budget;++j)bad+=text[(s+j)%text.size()]!=pattern[j];if(bad<=mismatch_budget)out.push_back(s);}return out;
''',
        r'''
require_case(cyclic_hamming_starts("abc","cab",0).value()==std::vector<std::size_t>{2});
require_case(cyclic_hamming_starts("ab","ababa",0).value()==std::vector<std::size_t>{0});
require_case(cyclic_hamming_starts("abc","acc",1).value()==std::vector<std::size_t>{0});
require_case(cyclic_hamming_starts("aa","b",1).value()==(std::vector<std::size_t>{0,1}));
require_case(!cyclic_hamming_starts("","x",0));
''',
        ("both strings are nonempty", "starts are text indices", "pattern can wrap repeatedly", "budget is inclusive", "results are ascending"),
        "bounded mismatch scan over modular indices", ("circular-string", "hamming", "matching"),
    )
    add(
        "Circular Buffer", "quota-lane-drain", "Quota lane drain",
        "Drain FIFO lanes in repeating lane-index order. Each visit may emit up to that lane's positive quota; zero-lane input is valid. Reject lane/quota size mismatch or any zero quota.",
        "", "std::optional<std::vector<int>> drain_fifo_lanes(std::vector<std::deque<int>> lanes, const std::vector<std::size_t>& quotas)",
        r'''
if(lanes.size()!=quotas.size()||std::any_of(quotas.begin(),quotas.end(),[](std::size_t q){return q==0;}))return std::nullopt;std::vector<int> out;std::size_t remain=0;for(const auto&l:lanes)remain+=l.size();while(remain){for(std::size_t i=0;i<lanes.size();++i)for(std::size_t k=0;k<quotas[i]&&!lanes[i].empty();++k){out.push_back(lanes[i].front());lanes[i].pop_front();--remain;}}return out;
''',
        r'''
require_case(drain_fifo_lanes({{1,2,3},{9,8}},{2,1}).value()==std::vector<int>({1,2,9,3,8}));
require_case(drain_fifo_lanes({},{}).value().empty());
require_case(drain_fifo_lanes({{}, {1}},{1,2}).value()==std::vector<int>{1});
require_case(!drain_fifo_lanes({{1}},{0}));
require_case(!drain_fifo_lanes({{1}},{}));
''',
        ("lane and quota counts match", "all quotas are positive", "empty lanes are skipped", "lane order repeats", "FIFO order is preserved per lane"),
        "round-robin lane visits with bounded per-visit drain", ("circular-scheduling", "fifo", "quota"),
    )

    # Clock: recurring schedules, rate fitting, and interval normalization.
    add(
        "Clock", "weekly-recurrence-wait", "Weekly recurrence wait",
        "Given a current minute in a repeating 10080-minute week and candidate minute slots, return the strictly positive wait to the next occurrence. Slots must be unique and in range; an empty schedule rejects.",
        "", "std::optional<int> wait_to_next_weekly_slot(int current_minute, const std::vector<int>& slots)",
        r'''
if(current_minute<0||current_minute>=10080||slots.empty())return std::nullopt;std::set<int> unique;int best=10080;for(int s:slots){if(s<0||s>=10080||!unique.insert(s).second)return std::nullopt;int d=(s-current_minute+10080)%10080;if(d==0)d=10080;best=std::min(best,d);}return best;
''',
        r'''
require_case(wait_to_next_weekly_slot(100,{120,90})==20);
require_case(wait_to_next_weekly_slot(100,{100})==10080);
require_case(wait_to_next_weekly_slot(10079,{0})==1);
require_case(!wait_to_next_weekly_slot(0,{}));
require_case(!wait_to_next_weekly_slot(0,{1,1}));
''',
        ("current and slots are week-relative", "slots are unique", "the wait is strictly positive", "same slot means next week", "empty schedules reject"),
        "modular distance minimization with canonical range checks", ("weekly-clock", "recurrence", "modular-time"),
    )
    add(
        "Clock", "tick-rate-fit", "Tick rate fit",
        "Fit one exact rational tick rate from strictly increasing real-time samples paired with nondecreasing device ticks. Return the reduced nonnegative numerator and positive denominator, or reject if successive sample slopes differ.",
        "struct TickSample { std::int64_t real_time; std::int64_t device_ticks; };", "std::optional<std::pair<std::int64_t,std::int64_t>> fit_exact_tick_rate(const std::vector<TickSample>& samples)",
        r'''
if(samples.size()<2)return std::nullopt;std::int64_t rn=0,rd=1;for(std::size_t i=1;i<samples.size();++i){auto dt=samples[i].real_time-samples[i-1].real_time;auto dk=samples[i].device_ticks-samples[i-1].device_ticks;if(dt<=0||dk<0)return std::nullopt;auto g=std::gcd(dk,dt);auto n=dk/g,d=dt/g;if(i==1){rn=n;rd=d;}else if(n!=rn||d!=rd)return std::nullopt;}return std::pair<std::int64_t,std::int64_t>{rn,rd};
''',
        r'''
require_case(fit_exact_tick_rate({{0,0},{2,3},{4,6}}).value()==std::pair<std::int64_t,std::int64_t>{3,2});
require_case(fit_exact_tick_rate({{1,5},{3,5}}).value()==std::pair<std::int64_t,std::int64_t>{0,1});
require_case(!fit_exact_tick_rate({{0,0}}));
require_case(!fit_exact_tick_rate({{0,0},{0,1}}));
require_case(!fit_exact_tick_rate({{0,0},{2,2},{3,4}}));
''',
        ("at least two samples", "real time strictly increases", "device ticks never decrease", "all adjacent reduced slopes match", "zero rate is 0/1"),
        "reduce and compare each adjacent rational slope", ("clock-drift", "rational-fit", "samples"),
    )
    add(
        "Clock", "stopwatch-interval-union", "Stopwatch interval union",
        "Normalize closed stopwatch intervals with nonnegative endpoints. Sort them and merge overlaps or intervals whose integer endpoints touch; return merged intervals and their inclusive total tick count.",
        "", "std::optional<std::pair<std::vector<std::pair<std::int64_t,std::int64_t>>,std::int64_t>> merge_stopwatch_intervals(std::vector<std::pair<std::int64_t,std::int64_t>> intervals)",
        r'''
for(auto [a,b]:intervals)if(a<0||a>b)return std::nullopt;std::sort(intervals.begin(),intervals.end());std::vector<std::pair<std::int64_t,std::int64_t>> out;for(auto p:intervals){if(out.empty()||p.first>out.back().second+1)out.push_back(p);else out.back().second=std::max(out.back().second,p.second);}std::int64_t total=0;for(auto [a,b]:out){if(b-a==std::numeric_limits<std::int64_t>::max()||total>std::numeric_limits<std::int64_t>::max()-(b-a+1))return std::nullopt;total+=b-a+1;}return std::pair{out,total};
''',
        r'''
require_case(merge_stopwatch_intervals({{4,5},{1,3},{9,9}}).value().first==(std::vector<std::pair<std::int64_t,std::int64_t>>{{1,5},{9,9}}));
require_case(merge_stopwatch_intervals({{4,5},{1,3},{9,9}}).value().second==6);
require_case(merge_stopwatch_intervals({}).value().second==0);
require_case(!merge_stopwatch_intervals({{2,1}}));
require_case(!merge_stopwatch_intervals({{-1,2}}));
''',
        ("intervals are closed", "endpoints are nonnegative", "adjacent integer intervals merge", "output is sorted and disjoint", "total count is overflow-checked"),
        "sort-and-sweep interval union with checked inclusive lengths", ("stopwatch", "interval-union", "overflow"),
    )

    # Complex Numbers: spectral selection, curves, and Hermitian energy.
    add(
        "Complex Numbers", "selected-dft-bins", "Selected DFT bins",
        "Compute only requested DFT bins of a nonempty complex signal using the negative-angle convention. Bin indices must be unique and in range; return values in request order.",
        "", "std::optional<std::vector<std::complex<double>>> selected_dft_bins(const std::vector<std::complex<double>>& signal, const std::vector<std::size_t>& bins)",
        r'''
if(signal.empty())return std::nullopt;std::set<std::size_t> seen;std::vector<std::complex<double>> out;const double pi=std::acos(-1.0);for(auto k:bins){if(k>=signal.size()||!seen.insert(k).second)return std::nullopt;std::complex<double> sum{};for(std::size_t n=0;n<signal.size();++n){double a=-2*pi*static_cast<double>(k*n)/signal.size();sum+=signal[n]*std::complex<double>(std::cos(a),std::sin(a));}out.push_back(sum);}return out;
''',
        r'''
auto d=selected_dft_bins({{1,0},{1,0}}, {0,1}).value();require_case(std::abs(d[0]-std::complex<double>{2,0})<1e-9);require_case(std::abs(d[1])<1e-9);
require_case(selected_dft_bins({{3,4}},{}).value().empty());
require_case(!selected_dft_bins({},{}));
require_case(!selected_dft_bins({{1,0}},{1}));
require_case(!selected_dft_bins({{1,0}},{0,0}));
''',
        ("signal is nonempty", "bins are unique and valid", "negative exponential convention", "request order is preserved", "empty bin request is valid"),
        "direct selected-bin DFT summation", ("complex", "dft", "spectral"),
    )
    add(
        "Complex Numbers", "bezier-complex-samples", "Complex Bezier samples",
        "Evaluate a complex Bezier curve at requested exact rational parameters numerator/denominator in [0,1]. The control polygon is nonempty and denominators are positive.",
        "", "std::optional<std::vector<std::complex<double>>> sample_complex_bezier(const std::vector<std::complex<double>>& control, const std::vector<std::pair<std::int64_t,std::int64_t>>& parameters)",
        r'''
if(control.empty())return std::nullopt;std::vector<std::complex<double>> out;for(auto [n,d]:parameters){if(d<=0||n<0||n>d)return std::nullopt;double t=static_cast<double>(n)/d;auto work=control;for(std::size_t width=work.size();width>1;--width)for(std::size_t i=0;i+1<width;++i)work[i]=work[i]*(1-t)+work[i+1]*t;out.push_back(work[0]);}return out;
''',
        r'''
auto b=sample_complex_bezier({{0,0},{2,2}},{{0,1},{1,2},{1,1}}).value();require_case(std::abs(b[1]-std::complex<double>{1,1})<1e-9);
require_case(std::abs(b.front())<1e-9);require_case(std::abs(b.back()-std::complex<double>{2,2})<1e-9);
require_case(sample_complex_bezier({{4,1}},{}).value().empty());
require_case(!sample_complex_bezier({},{}));
require_case(!sample_complex_bezier({{0,0}},{{2,1}}));
''',
        ("control polygon is nonempty", "denominators are positive", "parameters lie in closed unit interval", "request order is preserved", "de Casteljau evaluation is used"),
        "stable de Casteljau interpolation in the complex plane", ("complex", "bezier", "rational-parameter"),
    )
    add(
        "Complex Numbers", "hermitian-energy", "Hermitian energy",
        "Validate a square Hermitian complex matrix within the supplied nonnegative tolerance and compute the real quadratic energy x* A x. Dimension mismatch or a residual imaginary energy above tolerance rejects.",
        "", "std::optional<double> hermitian_quadratic_energy(const std::vector<std::vector<std::complex<double>>>& matrix, const std::vector<std::complex<double>>& x, double tolerance)",
        r'''
if(tolerance<0||matrix.size()!=x.size())return std::nullopt;std::size_t n=x.size();for(const auto&r:matrix)if(r.size()!=n)return std::nullopt;for(std::size_t i=0;i<n;++i)for(std::size_t j=0;j<n;++j)if(std::abs(matrix[i][j]-std::conj(matrix[j][i]))>tolerance)return std::nullopt;std::complex<double> e{};for(std::size_t i=0;i<n;++i)for(std::size_t j=0;j<n;++j)e+=std::conj(x[i])*matrix[i][j]*x[j];if(std::abs(e.imag())>tolerance)return std::nullopt;return e.real();
''',
        r'''
require_case(std::abs(hermitian_quadratic_energy({{{2,0},{0,0}},{{0,0},{3,0}}},{{1,0},{2,0}},1e-9).value()-14)<1e-9);
require_case(hermitian_quadratic_energy({}, {},0)==0);
require_case(!hermitian_quadratic_energy({{{1,0},{1,0}},{{0,0},{1,0}}},{{1,0},{1,0}},0));
require_case(!hermitian_quadratic_energy({}, {},-1));
require_case(!hermitian_quadratic_energy({{{1,0}}},{},0));
''',
        ("matrix is square and dimension-matched", "tolerance is nonnegative", "Hermitian symmetry is tolerance-bound", "empty energy is zero", "imaginary residual must be within tolerance"),
        "pairwise Hermitian validation and explicit quadratic accumulation", ("complex", "hermitian", "quadratic-form"),
    )

    # Crypto Square: transposition, polynomial checksums, and finite-state cycles.
    add(
        "Crypto Square", "ragged-columnar-transpose", "Ragged columnar transpose",
        "Write text row-major into rows of a positive width, then read existing cells by a supplied permutation of all column indices. Return the transposed text; invalid widths or permutations reject.",
        "", "std::optional<std::string> ragged_columnar_transpose(std::string_view text, std::size_t width, const std::vector<std::size_t>& column_order)",
        r'''
if(width==0||column_order.size()!=width)return std::nullopt;std::vector<int> seen(width);for(auto c:column_order)if(c>=width||seen[c]++)return std::nullopt;std::string out;for(auto c:column_order)for(std::size_t p=c;p<text.size();p+=width)out.push_back(text[p]);return out;
''',
        r'''
require_case(ragged_columnar_transpose("abcdefg",3,{2,0,1})=="cfadgbe");
require_case(ragged_columnar_transpose("",2,{0,1})=="");
require_case(ragged_columnar_transpose("a",1,{0})=="a");
require_case(!ragged_columnar_transpose("x",0,{}));
require_case(!ragged_columnar_transpose("x",2,{0,0}));
''',
        ("width is positive", "order is a full permutation", "ragged missing cells are skipped", "bytes are preserved", "empty text is valid"),
        "column-permutation traversal of an implicit ragged grid", ("transposition", "ragged-grid", "permutation"),
    )
    add(
        "Crypto Square", "binary-crc-syndrome", "Binary CRC syndrome",
        "Compute the modulo-two polynomial remainder of a nonempty binary message after appending degree zero bits, using a binary generator whose first and last bits are one and length is at least two.",
        "", "std::optional<std::string> binary_crc_syndrome(std::string_view message, std::string_view generator)",
        r'''
auto binary=[](std::string_view s){return std::all_of(s.begin(),s.end(),[](char c){return c=='0'||c=='1';});};if(message.empty()||generator.size()<2||!binary(message)||!binary(generator)||generator.front()!='1'||generator.back()!='1')return std::nullopt;std::string work(message);work.append(generator.size()-1,'0');for(std::size_t i=0;i+generator.size()<=work.size();++i)if(work[i]=='1')for(std::size_t j=0;j<generator.size();++j)work[i+j]=work[i+j]==generator[j]?'0':'1';return work.substr(work.size()-(generator.size()-1));
''',
        r'''
require_case(binary_crc_syndrome("1101","1011")=="001");
require_case(binary_crc_syndrome("0","11")=="0");
require_case(!binary_crc_syndrome("","11"));
require_case(!binary_crc_syndrome("102","11"));
require_case(!binary_crc_syndrome("1","10"));
''',
        ("message is nonempty binary", "generator has degree at least one", "generator endpoints are one", "division is modulo two", "remainder width is degree"),
        "in-place polynomial long division over GF(2)", ("crc", "polynomial", "binary"),
    )
    add(
        "Crypto Square", "lfsr-cycle-report", "LFSR cycle report",
        "For a nonempty seed of at most twenty bits and a nonempty unique set of tap indices, repeatedly shift right and insert the XOR of tapped old bits at index zero. Return preperiod and period lengths.",
        "", "std::optional<std::pair<std::size_t,std::size_t>> lfsr_cycle_report(std::string_view seed, const std::vector<std::size_t>& taps)",
        r'''
if(seed.empty()||seed.size()>20||taps.empty()||!std::all_of(seed.begin(),seed.end(),[](char c){return c=='0'||c=='1';}))return std::nullopt;std::set<std::size_t> unique;for(auto t:taps)if(t>=seed.size()||!unique.insert(t).second)return std::nullopt;std::map<std::string,std::size_t> at;std::string state(seed);for(std::size_t step=0;;++step){auto [it,fresh]=at.emplace(state,step);if(!fresh)return std::pair<std::size_t,std::size_t>{it->second,step-it->second};char bit='0';for(auto t:taps)if(state[t]=='1')bit=bit=='0'?'1':'0';state=bit+state.substr(0,state.size()-1);}
''',
        r'''
require_case(lfsr_cycle_report("1",{0}).value()==std::pair<std::size_t,std::size_t>{0,1});
require_case(lfsr_cycle_report("00",{0}).value()==std::pair<std::size_t,std::size_t>{0,1});
require_case(lfsr_cycle_report("10",{0,1}).value().second>0);
require_case(!lfsr_cycle_report("",{0}));
require_case(!lfsr_cycle_report("10",{2}));
''',
        ("seed is one to twenty binary bits", "taps are nonempty unique valid indices", "tap XOR uses the old state", "shift inserts at index zero", "first repeated state defines the report"),
        "bounded first-seen map over the finite state space", ("lfsr", "cycle-detection", "binary-state"),
    )

    # Diamond: Manhattan ownership, lattice intersections, and erosion depth.
    add(
        "Diamond", "manhattan-voronoi-owners", "Manhattan Voronoi owners",
        "Assign each query point to the unique closest distinct site under Manhattan distance. Return the site index or -1 for a tie; duplicate sites or distance overflow reject.",
        "using LatticePoint = std::pair<std::int64_t,std::int64_t>;", "std::optional<std::vector<int>> manhattan_voronoi_owners(const std::vector<LatticePoint>& sites, const std::vector<LatticePoint>& queries)",
        r'''
if(std::set<LatticePoint>(sites.begin(),sites.end()).size()!=sites.size())return std::nullopt;std::vector<int> out;for(auto q:queries){if(sites.empty()){out.push_back(-1);continue;}std::uint64_t best=std::numeric_limits<std::uint64_t>::max();int owner=-1;bool tie=false;for(std::size_t i=0;i<sites.size();++i){auto delta=[](std::int64_t a,std::int64_t b)->std::optional<std::uint64_t>{if((b>0&&a<std::numeric_limits<std::int64_t>::min()+b)||(b<0&&a>std::numeric_limits<std::int64_t>::max()+b))return std::nullopt;auto d=a-b;return d<0?std::uint64_t(-(d+1))+1:std::uint64_t(d);};auto dx=delta(q.first,sites[i].first),dy=delta(q.second,sites[i].second);if(!dx||!dy||*dx>std::numeric_limits<std::uint64_t>::max()-*dy)return std::nullopt;auto d=*dx+*dy;if(d<best){best=d;owner=static_cast<int>(i);tie=false;}else if(d==best)tie=true;}out.push_back(tie?-1:owner);}return out;
''',
        r'''
require_case(manhattan_voronoi_owners({{0,0},{4,0}},{{1,0},{2,0}}).value()==std::vector<int>({0,-1}));
require_case(manhattan_voronoi_owners({},{{1,2}}).value()==std::vector<int>{-1});
require_case(manhattan_voronoi_owners({{0,0}},{}).value().empty());
require_case(!manhattan_voronoi_owners({{0,0},{0,0}},{}));
require_case(manhattan_voronoi_owners({{2,3}},{{2,3}}).value()==std::vector<int>{0});
''',
        ("sites are distinct", "queries preserve order", "ties return -1", "no sites also returns -1", "distance arithmetic is checked"),
        "direct nearest-site scan with explicit tie state", ("diamond-metric", "voronoi", "lattice"),
    )
    add(
        "Diamond", "diamond-intersection-lattice-count", "Diamond intersection lattice count",
        "Count integer lattice points contained in every closed Manhattan diamond. Radii must be nonnegative and at most 500; an empty set of diamonds rejects as unbounded.",
        "struct ManhattanDiamond { int row; int col; int radius; };", "std::optional<std::size_t> diamond_intersection_lattice_count(const std::vector<ManhattanDiamond>& diamonds)",
        r'''
if(diamonds.empty())return std::nullopt;for(const auto&d:diamonds)if(d.radius<0||d.radius>500)return std::nullopt;int lo_r=diamonds[0].row-diamonds[0].radius,hi_r=diamonds[0].row+diamonds[0].radius,lo_c=diamonds[0].col-diamonds[0].radius,hi_c=diamonds[0].col+diamonds[0].radius;std::size_t count=0;for(int r=lo_r;r<=hi_r;++r)for(int c=lo_c;c<=hi_c;++c)if(std::all_of(diamonds.begin(),diamonds.end(),[&](const auto&d){return std::abs(static_cast<long long>(r)-d.row)+std::abs(static_cast<long long>(c)-d.col)<=d.radius;}))++count;return count;
''',
        r'''
require_case(diamond_intersection_lattice_count({{0,0,1}})==5);
require_case(diamond_intersection_lattice_count({{0,0,1},{1,0,1}})==2);
require_case(diamond_intersection_lattice_count({{0,0,0},{1,0,0}})==0);
require_case(!diamond_intersection_lattice_count({}));
require_case(!diamond_intersection_lattice_count({{0,0,-1}}));
''',
        ("input is nonempty", "radii are in the bounded public domain", "diamonds are closed", "empty intersection returns zero", "count is over integer lattice points"),
        "bounded enumeration inside the first diamond with all-diamond predicates", ("diamond", "intersection", "lattice-count"),
    )
    add(
        "Diamond", "diamond-erosion-depths", "Diamond erosion depths",
        "For a nonempty rectangular grid of '#' and '.', give every filled cell its one-based Manhattan erosion depth: distance to the nearest empty cell or to outside the grid. Empty cells receive zero.",
        "", "std::optional<std::vector<std::vector<int>>> diamond_erosion_depths(const std::vector<std::string>& grid)",
        r'''
if(grid.empty()||grid[0].empty())return std::nullopt;std::size_t h=grid.size(),w=grid[0].size();for(const auto&r:grid)if(r.size()!=w||!std::all_of(r.begin(),r.end(),[](char c){return c=='#'||c=='.';}))return std::nullopt;std::vector<std::vector<int>> d(h,std::vector<int>(w,-1));std::queue<std::pair<int,int>> q;for(int r=0;r<(int)h;++r)for(int c=0;c<(int)w;++c)if(grid[r][c]=='.'){d[r][c]=0;q.push({r,c});}else if(r==0||c==0||r+1==(int)h||c+1==(int)w){d[r][c]=1;q.push({r,c});}const int dr[4]={1,-1,0,0},dc[4]={0,0,1,-1};while(!q.empty()){auto [r,c]=q.front();q.pop();for(int k=0;k<4;++k){int a=r+dr[k],b=c+dc[k];if(a>=0&&b>=0&&a<(int)h&&b<(int)w&&grid[a][b]=='#'&&d[a][b]<0){d[a][b]=d[r][c]+1;q.push({a,b});}}}return d;
''',
        r'''
require_case(diamond_erosion_depths({"###","###","###"}).value()[1][1]==2);
require_case(diamond_erosion_depths({".#"}).value()==std::vector<std::vector<int>>({{0,1}}));
require_case(diamond_erosion_depths({"#"}).value()[0][0]==1);
require_case(!diamond_erosion_depths({}));
require_case(!diamond_erosion_depths({"##","#"}));
''',
        ("grid is nonempty rectangular", "only two cell symbols are accepted", "outside is empty", "empty cells have zero", "filled depth is one-based"),
        "multi-source Manhattan distance propagation from empty and boundary layers", ("diamond-erosion", "grid", "bfs"),
    )

    # Grade School: capped rubrics, optimistic appeals, and paired comparisons.
    add(
        "Grade School", "rubric-cap-scores", "Rubric cap scores",
        "Score submissions against named positive rubric caps. Each submission supplies nonnegative criterion points, may omit criteria as zero, and may not name unknown criteria; cap each contribution and return totals by student.",
        "", "std::optional<std::map<std::string,std::int64_t>> score_capped_rubrics(const std::map<std::string,std::int64_t>& caps, const std::map<std::string,std::map<std::string,std::int64_t>>& submissions)",
        r'''
for(auto [k,v]:caps)if(k.empty()||v<=0)return std::nullopt;std::map<std::string,std::int64_t> out;for(const auto&[student,points]:submissions){if(student.empty())return std::nullopt;std::int64_t total=0;for(auto [name,value]:points){auto it=caps.find(name);if(it==caps.end()||value<0)return std::nullopt;auto add=std::min(value,it->second);if(total>std::numeric_limits<std::int64_t>::max()-add)return std::nullopt;total+=add;}out[student]=total;}return out;
''',
        r'''
require_case(score_capped_rubrics({{"code",5},{"test",3}},{{"ann",{{"code",9},{"test",2}}}}).value().at("ann")==7);
require_case(score_capped_rubrics({{"x",1}},{{"a",{}}}).value().at("a")==0);
require_case(score_capped_rubrics({{"x",1}},{}).value().empty());
require_case(!score_capped_rubrics({{"x",0}},{}));
require_case(!score_capped_rubrics({{"x",1}},{{"a",{{"y",1}}}}));
''',
        ("caps are named and positive", "students are named", "points are nonnegative", "unknown criteria reject", "each contribution is capped"),
        "validated sparse rubric accumulation with checked totals", ("grading", "rubric", "caps"),
    )
    add(
        "Grade School", "optimistic-appeal-replay", "Optimistic appeal replay",
        "Replay score appeals carrying a student, expected version, and signed delta. Every student begins at the supplied nonnegative score and version zero; a version mismatch or a score outside [0,100] rejects the whole replay.",
        "struct Appeal { std::string student; std::size_t expected_version; int delta; };", "std::optional<std::map<std::string,std::pair<int,std::size_t>>> replay_grade_appeals(const std::map<std::string,int>& initial, const std::vector<Appeal>& appeals)",
        r'''
std::map<std::string,std::pair<int,std::size_t>> state;for(auto [s,v]:initial){if(s.empty()||v<0||v>100)return std::nullopt;state[s]={v,0};}for(const auto&a:appeals){auto it=state.find(a.student);if(a.student.empty()||it==state.end()||it->second.second!=a.expected_version)return std::nullopt;long long next=static_cast<long long>(it->second.first)+a.delta;if(next<0||next>100)return std::nullopt;it->second={static_cast<int>(next),it->second.second+1};}return state;
''',
        r'''
require_case(replay_grade_appeals({{"a",70}},{{"a",0,5},{"a",1,-2}}).value().at("a")==std::pair<int,std::size_t>{73,2});
require_case(replay_grade_appeals({},{}).value().empty());
require_case(!replay_grade_appeals({{"a",70}},{{"a",1,2}}));
require_case(!replay_grade_appeals({{"a",100}},{{"a",0,1}}));
require_case(!replay_grade_appeals({{"a",-1}},{}));
''',
        ("initial scores are 0 through 100", "students must already exist", "versions start at zero", "expected versions must match", "updates remain in range"),
        "optimistic-concurrency ledger replay with fail-closed bounds", ("grade-appeal", "versioning", "transaction"),
    )
    add(
        "Grade School", "paired-cohort-deltas", "Paired cohort deltas",
        "Compare two named score maps that must contain exactly the same nonempty student set. Return improvement, equality, and decline counts plus the lower median signed delta after sorting.",
        "struct CohortDeltaSummary { std::size_t improved; std::size_t equal; std::size_t declined; int lower_median; };", "std::optional<CohortDeltaSummary> summarize_paired_cohort_deltas(const std::map<std::string,int>& before, const std::map<std::string,int>& after)",
        r'''
if(before.empty()||before.size()!=after.size())return std::nullopt;std::vector<int>d;CohortDeltaSummary s{0,0,0,0};for(auto [name,a]:before){auto it=after.find(name);if(name.empty()||it==after.end())return std::nullopt;long long x=static_cast<long long>(it->second)-a;if(x<std::numeric_limits<int>::min()||x>std::numeric_limits<int>::max())return std::nullopt;d.push_back(static_cast<int>(x));if(x>0)++s.improved;else if(x<0)++s.declined;else ++s.equal;}std::sort(d.begin(),d.end());s.lower_median=d[(d.size()-1)/2];return s;
''',
        r'''
auto s=summarize_paired_cohort_deltas({{"a",2},{"b",5},{"c",4}},{{"a",3},{"b",3},{"c",4}}).value();require_case(s.improved==1&&s.equal==1&&s.declined==1&&s.lower_median==0);
require_case(summarize_paired_cohort_deltas({{"a",1},{"b",1}},{{"a",3},{"b",0}}).value().lower_median==-1);
require_case(!summarize_paired_cohort_deltas({},{}));
require_case(!summarize_paired_cohort_deltas({{"a",1}},{{"b",1}}));
require_case(!summarize_paired_cohort_deltas({{"",1}},{{"",2}}));
''',
        ("cohorts are nonempty", "student key sets match exactly", "student names are nonempty", "deltas are checked", "even cohorts use the lower median"),
        "paired map join and order-statistic summary", ("cohort", "paired-analysis", "median"),
    )

    # Kindergarten Garden: crop rotations, row shadows, and crate assignment.
    add(
        "Kindergarten Garden", "crop-rotation-audit", "Crop rotation audit",
        "Audit rectangular season-by-plot crop labels. Labels are nonempty lowercase words, every season has the same positive plot count, and no plot may repeat a crop within the supplied positive lookback. Return violating season/plot indices.",
        "", "std::optional<std::vector<std::pair<std::size_t,std::size_t>>> audit_crop_rotation(const std::vector<std::vector<std::string>>& seasons, std::size_t lookback)",
        r'''
if(seasons.empty()||seasons[0].empty()||lookback==0)return std::nullopt;std::size_t plots=seasons[0].size();std::vector<std::pair<std::size_t,std::size_t>> out;for(std::size_t s=0;s<seasons.size();++s){if(seasons[s].size()!=plots)return std::nullopt;for(std::size_t p=0;p<plots;++p){const auto&crop=seasons[s][p];if(crop.empty()||!std::all_of(crop.begin(),crop.end(),[](char c){return c>='a'&&c<='z';}))return std::nullopt;std::size_t begin=s>lookback?s-lookback:0;for(std::size_t q=begin;q<s;++q)if(seasons[q][p]==crop){out.push_back({s,p});break;}}}return out;
''',
        r'''
require_case(audit_crop_rotation({{"pea","corn"},{"bean","corn"}},1).value()==(std::vector<std::pair<std::size_t,std::size_t>>{{1,1}}));
require_case(audit_crop_rotation({{"a"},{"b"},{"a"}},1).value().empty());
require_case(audit_crop_rotation({{"a"},{"b"},{"a"}},2).value()==(std::vector<std::pair<std::size_t,std::size_t>>{{2,0}}));
require_case(!audit_crop_rotation({},1));
require_case(!audit_crop_rotation({{"A"}},1));
''',
        ("at least one season and plot", "lookback is positive", "shape is rectangular", "crop labels are lowercase words", "violations are season-major"),
        "bounded per-plot history scan", ("garden", "crop-rotation", "audit"),
    )
    add(
        "Kindergarten Garden", "eastward-shadow-profile", "Eastward shadow profile",
        "For nonnegative plant heights in west-to-east order and a positive integer sun slope, mark each plant shadowed when some western plant's remaining height after slope decay is strictly greater than its height.",
        "", "std::optional<std::vector<bool>> eastward_shadow_profile(const std::vector<int>& heights, int slope)",
        r'''
if(slope<=0||std::any_of(heights.begin(),heights.end(),[](int h){return h<0;}))return std::nullopt;std::vector<bool> out(heights.size());long long best=std::numeric_limits<long long>::min();for(std::size_t i=0;i<heights.size();++i){auto projected=static_cast<long long>(heights[i])+static_cast<long long>(slope)*static_cast<long long>(i);out[i]=best>projected;best=std::max(best,projected);}return out;
''',
        r'''
require_case(eastward_shadow_profile({5,2,2},1).value()==std::vector<bool>({false,true,true}));
require_case(eastward_shadow_profile({1,2,3},1).value()==std::vector<bool>({false,false,false}));
require_case(eastward_shadow_profile({},2).value().empty());
require_case(!eastward_shadow_profile({1},0));
require_case(!eastward_shadow_profile({-1},1));
''',
        ("heights are nonnegative", "slope is positive", "only western plants cast eastward", "equality is not shadow", "output aligns with input"),
        "running maximum of height plus distance compensation", ("garden", "shadow", "profile"),
    )
    add(
        "Kindergarten Garden", "harvest-crate-first-fit", "Harvest crate first fit",
        "Place positive harvest weights into identical positive-capacity crates using first-fit in input order. Return zero-based crate indices per item; an overweight item or checked-sum overflow rejects.",
        "", "std::optional<std::vector<std::size_t>> first_fit_harvest_crates(const std::vector<std::int64_t>& weights, std::int64_t capacity)",
        r'''
if(capacity<=0)return std::nullopt;std::vector<std::int64_t> used;std::vector<std::size_t> out;for(auto w:weights){if(w<=0||w>capacity)return std::nullopt;std::size_t i=0;while(i<used.size()&&used[i]>capacity-w)++i;if(i==used.size())used.push_back(0);used[i]+=w;out.push_back(i);}return out;
''',
        r'''
require_case(first_fit_harvest_crates({6,4,5,5},10).value()==std::vector<std::size_t>({0,0,1,1}));
require_case(first_fit_harvest_crates({},10).value().empty());
require_case(first_fit_harvest_crates({4,7,3},10).value()==std::vector<std::size_t>({0,1,0}));
require_case(!first_fit_harvest_crates({11},10));
require_case(!first_fit_harvest_crates({1},0));
''',
        ("capacity and weights are positive", "overweight items reject", "items retain input order", "lowest fitting crate wins", "new crates are appended"),
        "online first-fit bin assignment with checked remaining capacity", ("garden", "bin-packing", "first-fit"),
    )

    # Linked List: binary lifting, persistent-tail joins, and stable relinking.
    add(
        "Linked List", "successor-jump-queries", "Successor jump queries",
        "Answer successor queries on a functional linked structure. Each next index is -1 or valid; queries contain a start index and nonnegative step count. Return -1 if the chain ends before all steps.",
        "struct JumpQuery { int start; std::uint64_t steps; };", "std::optional<std::vector<int>> successor_jump_queries(const std::vector<int>& next, const std::vector<JumpQuery>& queries)",
        r'''
for(int n:next)if(n<-1||n>=static_cast<int>(next.size()))return std::nullopt;std::vector<std::vector<int>> up(64,next);for(int b=1;b<64;++b)for(std::size_t i=0;i<next.size();++i)up[b][i]=up[b-1][i]<0?-1:up[b-1][up[b-1][i]];std::vector<int> out;for(auto q:queries){if(q.start<0||q.start>=static_cast<int>(next.size()))return std::nullopt;int at=q.start;for(int b=0;b<64&&at>=0;++b)if(q.steps&(std::uint64_t{1}<<b))at=up[b][at];out.push_back(at);}return out;
''',
        r'''
require_case(successor_jump_queries({1,2,-1},{{0,0},{0,2},{0,3}}).value()==std::vector<int>({0,2,-1}));
require_case(successor_jump_queries({0},{{0,999}}).value()==std::vector<int>{0});
require_case(successor_jump_queries({},{}).value().empty());
require_case(!successor_jump_queries({2},{}));
require_case(!successor_jump_queries({-1},{{1,0}}));
''',
        ("next indices are -1 or valid", "starts are valid", "zero steps returns the start", "cycles are supported", "ended chains remain -1"),
        "64-level successor doubling table", ("linked-list", "binary-lifting", "queries"),
    )
    add(
        "Linked List", "persistent-common-tail", "Persistent common tail",
        "In an immutable acyclic next-index arena, return the first shared node of two head paths, or -1. Heads may be -1; invalid indices, cycles, or unreachable cycles anywhere in the arena reject.",
        "", "std::optional<int> persistent_common_tail(const std::vector<int>& next, int first_head, int second_head)",
        r'''
auto valid=[&](int x){return x>=-1&&x<static_cast<int>(next.size());};if(!valid(first_head)||!valid(second_head))return std::nullopt;for(int x:next)if(!valid(x))return std::nullopt;std::vector<int> state(next.size());std::function<bool(int)> dfs=[&](int i){if(i<0)return true;if(state[i]==1)return false;if(state[i]==2)return true;state[i]=1;if(!dfs(next[i]))return false;state[i]=2;return true;};for(std::size_t i=0;i<next.size();++i)if(!dfs(static_cast<int>(i)))return std::nullopt;std::set<int> path;for(int i=first_head;i>=0;i=next[i])path.insert(i);for(int i=second_head;i>=0;i=next[i])if(path.count(i))return i;return -1;
''',
        r'''
require_case(persistent_common_tail({2,2,3,-1},0,1)==2);
require_case(persistent_common_tail({1,-1,3,-1},0,2)==-1);
require_case(persistent_common_tail({},-1,-1)==-1);
require_case(!persistent_common_tail({0},0,-1));
require_case(!persistent_common_tail({2},0,-1));
''',
        ("all arena links are valid", "the entire arena is acyclic", "heads may be -1", "first shared node follows the second path", "disjoint paths return -1"),
        "global acyclicity proof followed by path-set intersection", ("persistent-list", "common-tail", "arena-audit"),
    )
    add(
        "Linked List", "stable-bucket-relink", "Stable bucket relink",
        "Relink array-indexed nodes into one chain ordered by nonnegative bucket number while preserving original index order within each bucket. Return the head and next-index array; bucket values above the declared count reject.",
        "", "std::optional<std::pair<int,std::vector<int>>> stable_bucket_relink(const std::vector<std::size_t>& buckets, std::size_t bucket_count)",
        r'''
std::vector<std::vector<int>> groups(bucket_count);for(std::size_t i=0;i<buckets.size();++i){if(buckets[i]>=bucket_count)return std::nullopt;groups[buckets[i]].push_back(static_cast<int>(i));}std::vector<int> order;for(const auto&g:groups)order.insert(order.end(),g.begin(),g.end());std::vector<int> next(buckets.size(),-1);for(std::size_t i=1;i<order.size();++i)next[order[i-1]]=order[i];return std::pair<int,std::vector<int>>{order.empty()?-1:order[0],next};
''',
        r'''
require_case(stable_bucket_relink({1,0,1,0},2).value()==std::pair<int,std::vector<int>>{1,{2,3,-1,0}});
require_case(stable_bucket_relink({},0).value().first==-1);
require_case(stable_bucket_relink({0,0},1).value().second==std::vector<int>({1,-1}));
require_case(!stable_bucket_relink({0},0));
require_case(!stable_bucket_relink({2},2));
''',
        ("bucket indices are in range", "empty nodes allow zero buckets", "bucket order is ascending", "within-bucket order is stable", "the final node links to -1"),
        "stable bucket collection followed by index-chain construction", ("linked-list", "stable-partition", "relink"),
    )

    # Parallel Letter Frequency: parallel canonicalization and indexed reductions.
    add(
        "Parallel Letter Frequency", "parallel-anagram-groups", "Parallel anagram groups",
        "Group nonempty lowercase words by exact letter multiset using at most the requested positive worker count. Sort words inside groups and sort groups by their first word.",
        "", "std::optional<std::vector<std::vector<std::string>>> parallel_anagram_groups(const std::vector<std::string>& words, std::size_t workers)",
        r'''
if(workers==0)return std::nullopt;for(const auto&w:words)if(w.empty()||!std::all_of(w.begin(),w.end(),[](char c){return c>='a'&&c<='z';}))return std::nullopt;std::size_t jobs=std::min(workers,std::max<std::size_t>(1,words.size()));std::vector<std::future<std::map<std::string,std::vector<std::string>>>> fs;for(std::size_t j=0;j<jobs;++j)fs.push_back(std::async(std::launch::async,[&,j]{std::map<std::string,std::vector<std::string>> m;for(std::size_t i=j;i<words.size();i+=jobs){auto key=words[i];std::sort(key.begin(),key.end());m[key].push_back(words[i]);}return m;}));std::map<std::string,std::vector<std::string>> all;for(auto&f:fs)for(auto&[k,v]:f.get())all[k].insert(all[k].end(),v.begin(),v.end());std::vector<std::vector<std::string>> out;for(auto&[k,v]:all){std::sort(v.begin(),v.end());out.push_back(v);}std::sort(out.begin(),out.end(),[](const auto&a,const auto&b){return a[0]<b[0];});return out;
''',
        r'''
require_case(parallel_anagram_groups({"tea","ate","bat"},2).value()==(std::vector<std::vector<std::string>>{{"ate","tea"},{"bat"}}));
require_case(parallel_anagram_groups({},3).value().empty());
require_case(parallel_anagram_groups({"a"},9).value()==(std::vector<std::vector<std::string>>{{"a"}}));
require_case(!parallel_anagram_groups({"A"},1));
require_case(!parallel_anagram_groups({"a"},0));
''',
        ("worker count is positive", "words are nonempty lowercase", "workers are bounded by useful jobs", "groups and members are canonical", "empty input is valid"),
        "striped asynchronous map construction and deterministic reduction", ("parallel", "anagram", "deterministic-reduction"),
    )
    add(
        "Parallel Letter Frequency", "parallel-caesar-coincidences", "Parallel Caesar coincidences",
        "For equal-length lowercase strings, count aligned character matches under every Caesar shift 0 through 25 using positive workers. Return 26 counts in shift order.",
        "", "std::optional<std::array<std::size_t,26>> parallel_caesar_coincidences(std::string_view left, std::string_view right, std::size_t workers)",
        r'''
if(workers==0||left.size()!=right.size()||!std::all_of(left.begin(),left.end(),[](char c){return c>='a'&&c<='z';})||!std::all_of(right.begin(),right.end(),[](char c){return c>='a'&&c<='z';}))return std::nullopt;std::size_t jobs=std::min<std::size_t>(workers,26);std::vector<std::future<std::vector<std::pair<int,std::size_t>>>> fs;for(std::size_t j=0;j<jobs;++j)fs.push_back(std::async(std::launch::async,[&,j]{std::vector<std::pair<int,std::size_t>> v;for(int s=static_cast<int>(j);s<26;s+=jobs){std::size_t n=0;for(std::size_t i=0;i<left.size();++i)n+=((left[i]-'a'+s)%26)==right[i]-'a';v.push_back({s,n});}return v;}));std::array<std::size_t,26> out{};for(auto&f:fs)for(auto [s,n]:f.get())out[s]=n;return out;
''',
        r'''
auto c=parallel_caesar_coincidences("abc","bcd",4).value();require_case(c[1]==3&&c[0]==0);
require_case(parallel_caesar_coincidences("","",1).value()[0]==0);
require_case(parallel_caesar_coincidences("z","a",30).value()[1]==1);
require_case(!parallel_caesar_coincidences("a","aa",1));
require_case(!parallel_caesar_coincidences("A","a",1));
''',
        ("worker count is positive", "strings have equal length", "bytes are lowercase letters", "all 26 shifts are computed", "output index equals shift"),
        "parallel partition over a fixed 26-shift reduction", ("parallel", "caesar", "coincidence"),
    )
    add(
        "Parallel Letter Frequency", "parallel-rare-offsets", "Parallel rare offsets",
        "Across lowercase lines, return every global byte offset whose letter occurs exactly once in the whole corpus. Lines are concatenated without separators and offsets are ascending; use positive workers.",
        "", "std::optional<std::vector<std::size_t>> parallel_rare_letter_offsets(const std::vector<std::string>& lines, std::size_t workers)",
        r'''
if(workers==0)return std::nullopt;for(const auto&s:lines)if(!std::all_of(s.begin(),s.end(),[](char c){return c>='a'&&c<='z';}))return std::nullopt;std::size_t jobs=std::min(workers,std::max<std::size_t>(1,lines.size()));std::vector<std::future<std::array<std::size_t,26>>> fs;for(std::size_t j=0;j<jobs;++j)fs.push_back(std::async(std::launch::async,[&,j]{std::array<std::size_t,26>a{};for(std::size_t i=j;i<lines.size();i+=jobs)for(char c:lines[i])++a[c-'a'];return a;}));std::array<std::size_t,26> total{};for(auto&f:fs){auto a=f.get();for(int i=0;i<26;++i)total[i]+=a[i];}std::vector<std::size_t> out;std::size_t offset=0;for(const auto&s:lines)for(char c:s){if(total[c-'a']==1)out.push_back(offset);++offset;}return out;
''',
        r'''
require_case(parallel_rare_letter_offsets({"ab","aca"},2).value()==std::vector<std::size_t>{1,3});
require_case(parallel_rare_letter_offsets({},3).value().empty());
require_case(parallel_rare_letter_offsets({""},1).value().empty());
require_case(!parallel_rare_letter_offsets({"A"},1));
require_case(!parallel_rare_letter_offsets({},0));
''',
        ("worker count is positive", "lines contain lowercase letters only", "concatenation has no separators", "rarity is corpus-global", "offsets are ascending"),
        "parallel frequency reduction followed by deterministic offset scan", ("parallel", "rare-letter", "offset"),
    )

    # Phone Number: keypad search, pulse billing, and prioritized contact merge.
    add(
        "Phone Number", "t9-prefix-suggestions", "T9 prefix suggestions",
        "Return up to limit contact names whose lowercase letters encode to a supplied nonempty T9 digit prefix. Names are unique nonempty lowercase words; prefix digits are 2 through 9; results are lexicographic.",
        "", "std::optional<std::vector<std::string>> t9_prefix_suggestions(const std::vector<std::string>& contacts, std::string_view prefix, std::size_t limit)",
        r'''
if(prefix.empty()||!std::all_of(prefix.begin(),prefix.end(),[](char c){return c>='2'&&c<='9';}))return std::nullopt;std::set<std::string> unique;auto digit=[](char c){const std::string groups="22233344455566677778889999";return groups[c-'a'];};std::vector<std::string> out;for(const auto&name:contacts){if(name.empty()||!std::all_of(name.begin(),name.end(),[](char c){return c>='a'&&c<='z';})||!unique.insert(name).second)return std::nullopt;if(name.size()>=prefix.size()&&std::equal(prefix.begin(),prefix.end(),name.begin(),[&](char d,char c){return d==digit(c);}))out.push_back(name);}std::sort(out.begin(),out.end());if(out.size()>limit)out.resize(limit);return out;
''',
        r'''
require_case(t9_prefix_suggestions({"tree","used","apple"},"873",9).value()==std::vector<std::string>({"tree","used"}));
require_case(t9_prefix_suggestions({"a"},"2",0).value().empty());
require_case(t9_prefix_suggestions({},"2",4).value().empty());
require_case(!t9_prefix_suggestions({"A"},"2",1));
require_case(!t9_prefix_suggestions({"a"},"1",1));
''',
        ("prefix is nonempty digits 2 through 9", "contacts are unique lowercase words", "prefix match is digit-wise", "results are lexicographic", "limit may be zero"),
        "deterministic keypad encoding filter and bounded canonical sort", ("phone", "t9", "prefix-search"),
    )
    add(
        "Phone Number", "billing-pulse-summary", "Billing pulse summary",
        "Bill positive-duration calls by positive whole-second pulses, rounding each call independently upward. Calls name nonempty accounts and have end greater than start; aggregate pulse counts with overflow checks.",
        "struct TimedCall { std::string account; std::int64_t start_second; std::int64_t end_second; };", "std::optional<std::map<std::string,std::int64_t>> summarize_billing_pulses(const std::vector<TimedCall>& calls, std::int64_t pulse_seconds)",
        r'''
if(pulse_seconds<=0)return std::nullopt;std::map<std::string,std::int64_t> out;for(const auto&c:calls){if(c.account.empty()||c.start_second<0||c.end_second<=c.start_second)return std::nullopt;auto duration=c.end_second-c.start_second;auto pulses=duration/pulse_seconds+(duration%pulse_seconds!=0);auto&v=out[c.account];if(v>std::numeric_limits<std::int64_t>::max()-pulses)return std::nullopt;v+=pulses;}return out;
''',
        r'''
require_case(summarize_billing_pulses({{"a",0,61},{"a",70,130}},60).value().at("a")==3);
require_case(summarize_billing_pulses({},30).value().empty());
require_case(summarize_billing_pulses({{"x",2,3}},10).value().at("x")==1);
require_case(!summarize_billing_pulses({{"",0,1}},1));
require_case(!summarize_billing_pulses({},0));
''',
        ("pulse size is positive", "accounts are nonempty", "times are nonnegative and increasing", "each call rounds independently", "account totals are checked"),
        "per-call ceiling division and checked keyed accumulation", ("phone", "billing", "rounding"),
    )
    add(
        "Phone Number", "contact-source-merge", "Contact source merge",
        "Merge contact records by unique nonempty lowercase name. Lower numeric priority wins; equal priority must agree on the digit-only nonempty number or reject. Return the winning number by name.",
        "struct ContactRecord { std::string name; std::string number; int priority; };", "std::optional<std::map<std::string,std::string>> merge_contact_sources(const std::vector<ContactRecord>& records)",
        r'''
std::map<std::string,std::pair<int,std::string>> best;for(const auto&r:records){if(r.name.empty()||r.number.empty()||!std::all_of(r.name.begin(),r.name.end(),[](char c){return c>='a'&&c<='z';})||!std::all_of(r.number.begin(),r.number.end(),[](char c){return c>='0'&&c<='9';})||r.priority<0)return std::nullopt;auto it=best.find(r.name);if(it==best.end()||r.priority<it->second.first)best[r.name]={r.priority,r.number};else if(r.priority==it->second.first&&r.number!=it->second.second)return std::nullopt;}std::map<std::string,std::string> out;for(auto&[n,p]:best)out[n]=p.second;return out;
''',
        r'''
require_case(merge_contact_sources({{"ann","111",2},{"ann","222",1}}).value().at("ann")=="222");
require_case(merge_contact_sources({{"ann","111",1},{"ann","111",1}}).value().at("ann")=="111");
require_case(merge_contact_sources({}).value().empty());
require_case(!merge_contact_sources({{"Ann","1",0}}));
require_case(!merge_contact_sources({{"a","1",0},{"a","2",0}}));
''',
        ("names are lowercase words", "numbers are nonempty digits", "priorities are nonnegative", "lower priority value wins", "equal-priority conflict rejects"),
        "priority-aware stable map merge with conflict detection", ("phone", "contact-merge", "priority"),
    )

    # Spiral Matrix: voxel shells, turn replays, and hexagonal rings.
    add(
        "Spiral Matrix", "voxel-shell-sums", "Voxel shell sums",
        "For a nonempty rectangular 3D integer box, sum cells by zero-based shell depth, where depth is the minimum distance to any of the six faces. Return outer-to-inner checked int64 sums.",
        "", "std::optional<std::vector<std::int64_t>> voxel_shell_sums(const std::vector<std::vector<std::vector<int>>>& box)",
        r'''
if(box.empty()||box[0].empty()||box[0][0].empty())return std::nullopt;std::size_t z=box.size(),y=box[0].size(),x=box[0][0].size();for(const auto&plane:box){if(plane.size()!=y)return std::nullopt;for(const auto&row:plane)if(row.size()!=x)return std::nullopt;}std::size_t shells=(std::min({z,y,x})+1)/2;std::vector<std::int64_t> out(shells);for(std::size_t a=0;a<z;++a)for(std::size_t b=0;b<y;++b)for(std::size_t c=0;c<x;++c){auto d=std::min({a,z-1-a,b,y-1-b,c,x-1-c});auto v=box[a][b][c];if((v>0&&out[d]>std::numeric_limits<std::int64_t>::max()-v)||(v<0&&out[d]<std::numeric_limits<std::int64_t>::min()-v))return std::nullopt;out[d]+=v;}return out;
''',
        r'''
require_case(voxel_shell_sums({{{1,2},{3,4}}}).value()==std::vector<std::int64_t>{10});
std::vector<std::vector<std::vector<int>>> cube(3,std::vector<std::vector<int>>(3,std::vector<int>(3,1)));require_case(voxel_shell_sums(cube).value()==std::vector<std::int64_t>({26,1}));
require_case(!voxel_shell_sums({}));
require_case(!voxel_shell_sums({{}}));
require_case(!voxel_shell_sums({{{1}},{{1,2}}}));
''',
        ("box is nonempty in every dimension", "shape is rectangular", "depth uses all six faces", "output is outer-to-inner", "sums are int64 checked"),
        "single voxel scan classified by minimum face distance", ("spiral", "voxel-shell", "3d-grid"),
    )
    add(
        "Spiral Matrix", "turn-command-self-avoidance", "Turn command self avoidance",
        "Replay commands L, R, and F from origin facing north. Turns rotate in place; F advances one lattice step. Return every visited position including origin, or reject the first repeated position or invalid command.",
        "using GridPoint = std::pair<int,int>;", "std::optional<std::vector<GridPoint>> replay_self_avoiding_turns(std::string_view commands)",
        r'''
int r=0,c=0,dir=0;const int dr[4]={-1,0,1,0},dc[4]={0,1,0,-1};std::set<GridPoint> seen{{0,0}};std::vector<GridPoint> out{{0,0}};for(char ch:commands){if(ch=='L')dir=(dir+3)%4;else if(ch=='R')dir=(dir+1)%4;else if(ch=='F'){if((dr[dir]<0&&r==std::numeric_limits<int>::min())||(dr[dir]>0&&r==std::numeric_limits<int>::max())||(dc[dir]<0&&c==std::numeric_limits<int>::min())||(dc[dir]>0&&c==std::numeric_limits<int>::max()))return std::nullopt;r+=dr[dir];c+=dc[dir];if(!seen.insert({r,c}).second)return std::nullopt;out.push_back({r,c});}else return std::nullopt;}return out;
''',
        r'''
require_case(replay_self_avoiding_turns("FFRFF").value().back()==GridPoint{-2,2});
require_case(replay_self_avoiding_turns("").value()==std::vector<GridPoint>{{0,0}});
require_case(replay_self_avoiding_turns("LLLL").value().size()==1);
require_case(!replay_self_avoiding_turns("FRFRFRF"));
require_case(!replay_self_avoiding_turns("X"));
''',
        ("origin is included", "turns do not visit a new point", "movement is unit cardinal", "repeated positions reject", "invalid commands reject"),
        "direction-state replay with a visited lattice set", ("spiral", "turns", "self-avoiding-walk"),
    )
    add(
        "Spiral Matrix", "hex-ring-coordinate", "Hex ring coordinate",
        "Return axial (q,r) coordinates after a nonnegative number of steps along a hexagonal outward ring walk: step zero is origin; each ring starts at (ring,0) and walks NW, W, SW, SE, E, NE.",
        "using AxialPoint = std::pair<int,int>;", "std::optional<AxialPoint> hex_ring_coordinate(std::uint64_t steps)",
        r'''
if(steps==0)return AxialPoint{0,0};std::uint64_t ring=1,base=1;while(steps>=base+6*ring){base+=6*ring;++ring;if(ring>static_cast<std::uint64_t>(std::numeric_limits<int>::max()))return std::nullopt;}std::uint64_t offset=steps-base;long long q=ring,r=0;const int dq[6]={-1,-1,0,1,1,0},dr[6]={1,0,-1,-1,0,1};for(int side=0;side<6;++side){auto take=std::min<std::uint64_t>(ring,offset);q+=dq[side]*static_cast<long long>(take);r+=dr[side]*static_cast<long long>(take);offset-=take;if(!offset)break;}if(q<std::numeric_limits<int>::min()||q>std::numeric_limits<int>::max()||r<std::numeric_limits<int>::min()||r>std::numeric_limits<int>::max())return std::nullopt;return AxialPoint{static_cast<int>(q),static_cast<int>(r)};
''',
        r'''
require_case(hex_ring_coordinate(0)==AxialPoint{0,0});
require_case(hex_ring_coordinate(1)==AxialPoint{1,0});
require_case(hex_ring_coordinate(2)==AxialPoint{0,1});
require_case(hex_ring_coordinate(6)==AxialPoint{1,-1});
require_case(hex_ring_coordinate(7)==AxialPoint{2,0});
''',
        ("steps are zero-based", "ring one occupies steps 1 through 6", "axial direction order is frozen", "ring starts are positive q-axis", "unrepresentable coordinates reject"),
        "locate a cumulative hex ring then walk at most six sides", ("spiral", "hex-grid", "ring-coordinate"),
    )

    # Sublist: wildcard matching, collision-confirmed hashing, and block covers.
    add(
        "Sublist", "wildcard-contiguous-matches", "Wildcard contiguous matches",
        "Return all start indices where a nonempty pattern matches contiguously in a text, with '?' matching exactly one byte. Empty text is valid; starts are ascending.",
        "", "std::optional<std::vector<std::size_t>> wildcard_contiguous_matches(std::string_view text, std::string_view pattern)",
        r'''
if(pattern.empty())return std::nullopt;std::vector<std::size_t> out;if(pattern.size()>text.size())return out;for(std::size_t i=0;i+pattern.size()<=text.size();++i){bool ok=true;for(std::size_t j=0;j<pattern.size();++j)if(pattern[j]!='?'&&pattern[j]!=text[i+j]){ok=false;break;}if(ok)out.push_back(i);}return out;
''',
        r'''
require_case(wildcard_contiguous_matches("abac","a?").value()==std::vector<std::size_t>({0,2}));
require_case(wildcard_contiguous_matches("aaa","aa").value()==std::vector<std::size_t>({0,1}));
require_case(wildcard_contiguous_matches("","a").value().empty());
require_case(wildcard_contiguous_matches("a","??").value().empty());
require_case(!wildcard_contiguous_matches("a",""));
''',
        ("pattern is nonempty", "question mark consumes one byte", "matches may overlap", "too-long patterns have no matches", "starts are ascending"),
        "direct aligned scan with a one-byte wildcard", ("sublist", "wildcard", "contiguous"),
    )
    add(
        "Sublist", "confirmed-rolling-hash-matches", "Confirmed rolling hash matches",
        "Find every exact byte substring occurrence using a supplied odd base greater than one and uint64 wraparound rolling hashes. Every hash hit must be confirmed byte-for-byte; an empty pattern rejects.",
        "", "std::optional<std::vector<std::size_t>> confirmed_rolling_hash_matches(std::string_view text, std::string_view pattern, std::uint64_t base)",
        r'''
if(pattern.empty()||base<=1||base%2==0)return std::nullopt;std::vector<std::size_t> out;if(pattern.size()>text.size())return out;std::uint64_t hp=0,hw=0,power=1;for(std::size_t i=0;i<pattern.size();++i){hp=hp*base+static_cast<unsigned char>(pattern[i])+1;hw=hw*base+static_cast<unsigned char>(text[i])+1;if(i+1<pattern.size())power*=base;}for(std::size_t i=0;;++i){if(hw==hp&&text.substr(i,pattern.size())==pattern)out.push_back(i);if(i+pattern.size()==text.size())break;hw-=power*(static_cast<unsigned char>(text[i])+1);hw=hw*base+static_cast<unsigned char>(text[i+pattern.size()])+1;}return out;
''',
        r'''
require_case(confirmed_rolling_hash_matches("ababa","aba",257).value()==std::vector<std::size_t>({0,2}));
require_case(confirmed_rolling_hash_matches("aaa","a",3).value()==std::vector<std::size_t>({0,1,2}));
require_case(confirmed_rolling_hash_matches("","a",3).value().empty());
require_case(!confirmed_rolling_hash_matches("a","",3));
require_case(!confirmed_rolling_hash_matches("a","a",2));
''',
        ("pattern is nonempty", "base is odd and above one", "uint64 wraparound is intentional", "hash hits are byte-confirmed", "overlaps are retained"),
        "Rabin-Karp rolling candidate filter with mandatory exact confirmation", ("sublist", "rolling-hash", "collision-defense"),
    )
    add(
        "Sublist", "minimum-substring-block-cover", "Minimum substring block cover",
        "Split a nonempty target into the fewest nonempty consecutive blocks such that every block occurs contiguously in the source. Return that minimum count, or an empty optional when impossible; malformed empty target rejects via the outer optional.",
        "struct BlockCoverResult { bool possible; std::size_t blocks; };", "std::optional<BlockCoverResult> minimum_substring_block_cover(std::string_view source, std::string_view target)",
        r'''
if(target.empty())return std::nullopt;const std::size_t inf=target.size()+1;std::vector<std::size_t> dp(target.size()+1,inf);dp[0]=0;for(std::size_t i=0;i<target.size();++i)if(dp[i]<inf)for(std::size_t j=i+1;j<=target.size();++j)if(source.find(target.substr(i,j-i))!=std::string_view::npos)dp[j]=std::min(dp[j],dp[i]+1);if(dp.back()==inf)return BlockCoverResult{false,0};return BlockCoverResult{true,dp.back()};
''',
        r'''
require_case(minimum_substring_block_cover("abc","abcabc").value().blocks==2);
require_case(minimum_substring_block_cover("abcd","ac").value().blocks==2);
require_case(!minimum_substring_block_cover("a",""));
require_case(!minimum_substring_block_cover("","a").value().possible);
require_case(minimum_substring_block_cover("xyz","xy").value().blocks==1);
''',
        ("target is nonempty", "blocks preserve target order", "each block is a source substring", "impossible has possible=false", "minimum block count is returned"),
        "prefix dynamic programming over source-substring membership", ("sublist", "block-cover", "dynamic-programming"),
    )

    # Yacht: postfix rules, canonical partitions, and histogram rerolls.
    add(
        "Yacht", "postfix-dice-rule", "Postfix dice rule",
        "Evaluate a postfix dice scoring program. Tokens are sum, max, count:N for face N in [1,6], nonnegative integer literals, and binary + or *. Dice faces must be 1 through 6; malformed stacks and checked arithmetic reject.",
        "", "std::optional<std::int64_t> evaluate_postfix_dice_rule(const std::vector<int>& dice, const std::vector<std::string>& program)",
        r'''
for(int d:dice)if(d<1||d>6)return std::nullopt;std::vector<std::int64_t> st;auto push_checked=[&](long long v){st.push_back(v);};for(const auto&t:program){if(t=="sum")st.push_back(std::accumulate(dice.begin(),dice.end(),std::int64_t{0}));else if(t=="max"){if(dice.empty())return std::nullopt;st.push_back(*std::max_element(dice.begin(),dice.end()));}else if(t.rfind("count:",0)==0&&t.size()==7&&t[6]>='1'&&t[6]<='6')st.push_back(std::count(dice.begin(),dice.end(),t[6]-'0'));else if(t=="+"||t=="*"){if(st.size()<2)return std::nullopt;auto b=st.back();st.pop_back();auto a=st.back();st.pop_back();if(t=="+"&&a>std::numeric_limits<std::int64_t>::max()-b)return std::nullopt;if(t=="*"&&a!=0&&b>std::numeric_limits<std::int64_t>::max()/a)return std::nullopt;push_checked(t=="+"?a+b:a*b);}else if(!t.empty()&&std::all_of(t.begin(),t.end(),[](char c){return c>='0'&&c<='9';})){std::uint64_t v=0;for(char c:t){auto digit=static_cast<std::uint64_t>(c-'0');auto limit=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());if(v>(limit-digit)/10)return std::nullopt;v=v*10+digit;}st.push_back(static_cast<std::int64_t>(v));}else return std::nullopt;}if(st.size()!=1)return std::nullopt;return st[0];
''',
        r'''
require_case(evaluate_postfix_dice_rule({1,1,3},{"sum","count:1","*"})==10);
require_case(evaluate_postfix_dice_rule({6},{"max","2","+"})==8);
require_case(!evaluate_postfix_dice_rule({},{"max"}));
require_case(!evaluate_postfix_dice_rule({0},{"sum"}));
require_case(!evaluate_postfix_dice_rule({1},{"1","1"}));
''',
        ("dice faces are 1 through 6", "program is postfix", "count syntax is exact", "max needs at least one die", "arithmetic and final stack shape are checked"),
        "typed stack-machine replay with dice-specific primitives", ("yacht", "postfix", "scoring-rule"),
    )
    add(
        "Yacht", "equal-sum-dice-partition", "Equal-sum dice partition",
        "Partition all positive dice values into two nonempty equal-sum groups. Return the lexicographically earliest vector of indices in the first group among solutions, considering a group and its complement equivalent by requiring index zero in the first group.",
        "", "std::optional<std::vector<std::size_t>> equal_sum_dice_partition(const std::vector<int>& dice)",
        r'''
if(dice.size()<2||dice.size()>24||std::any_of(dice.begin(),dice.end(),[](int x){return x<=0;}))return std::nullopt;long long total=std::accumulate(dice.begin(),dice.end(),0LL);if(total%2)return std::vector<std::size_t>{};std::vector<std::size_t> best;bool found=false;std::uint64_t limit=std::uint64_t{1}<<dice.size();for(std::uint64_t bits=1;bits+1<limit;++bits){if(!(bits&1))continue;long long sum=0;std::vector<std::size_t> pick;for(std::size_t i=0;i<dice.size();++i)if(bits&(std::uint64_t{1}<<i)){sum+=dice[i];pick.push_back(i);}if(sum*2==total&&(!found||pick<best)){best=pick;found=true;}}return best;
''',
        r'''
require_case(equal_sum_dice_partition({1,1}).value()==std::vector<std::size_t>{0});
require_case(equal_sum_dice_partition({1,2,3}).value()==std::vector<std::size_t>({0,1}));
require_case(equal_sum_dice_partition({1,2}).value().empty());
require_case(!equal_sum_dice_partition({1}));
require_case(!equal_sum_dice_partition({1,0}));
''',
        ("two to twenty-four positive values", "both groups are nonempty", "index zero breaks complement symmetry", "all dice are used", "no solution returns an empty inner vector"),
        "bounded subset enumeration with canonical complement and lexicographic witness", ("yacht", "partition", "witness"),
    )
    add(
        "Yacht", "exact-histogram-rerolls", "Exact histogram rerolls",
        "Given dice faces and a target count for every face 1 through sides, return the minimum dice that must be rerolled to make the exact histogram possible. Sides is positive, all faces are in range, counts are nonnegative, and target total equals dice count.",
        "", "std::optional<std::size_t> minimum_exact_histogram_rerolls(const std::vector<int>& dice, int sides, const std::vector<std::size_t>& target_counts)",
        r'''
if(sides<=0||target_counts.size()!=static_cast<std::size_t>(sides)||std::accumulate(target_counts.begin(),target_counts.end(),std::size_t{0})!=dice.size())return std::nullopt;std::vector<std::size_t> have(sides);for(int d:dice){if(d<1||d>sides)return std::nullopt;++have[d-1];}std::size_t keep=0;for(int f=0;f<sides;++f)keep+=std::min(have[f],target_counts[f]);return dice.size()-keep;
''',
        r'''
require_case(minimum_exact_histogram_rerolls({1,1,2},3,{1,1,1})==1);
require_case(minimum_exact_histogram_rerolls({2,2},2,{0,2})==0);
require_case(minimum_exact_histogram_rerolls({},1,{0})==0);
require_case(!minimum_exact_histogram_rerolls({1},0,{}));
require_case(!minimum_exact_histogram_rerolls({3},2,{1,0}));
''',
        ("sides is positive", "target has one count per face", "target total equals dice count", "dice faces are in range", "maximum already-useful dice are retained"),
        "histogram intersection determines the maximum keep set", ("yacht", "reroll", "histogram"),
    )

    # Zebra Puzzle: adjacency placement, Latin completion, and clue minimization.
    add(
        "Zebra Puzzle", "adjacency-placement-count", "Adjacency placement count",
        "Count permutations of n named items satisfying fixed-position and unordered-adjacency clues. Names are unique nonempty strings, positions are zero-based, clue names must exist, and duplicate constraints reject. n is at most ten.",
        "struct FixedPlacement { std::string item; std::size_t position; };", "std::optional<std::size_t> count_adjacency_placements(std::vector<std::string> items, const std::vector<FixedPlacement>& fixed, const std::vector<std::pair<std::string,std::string>>& adjacent)",
        r'''
if(items.size()>10||std::set<std::string>(items.begin(),items.end()).size()!=items.size()||std::any_of(items.begin(),items.end(),[](const auto&s){return s.empty();}))return std::nullopt;std::map<std::string,std::size_t> forced;std::set<std::size_t> used_pos;for(const auto&f:fixed)if(f.position>=items.size()||!std::count(items.begin(),items.end(),f.item)||!forced.emplace(f.item,f.position).second||!used_pos.insert(f.position).second)return std::nullopt;std::set<std::pair<std::string,std::string>> clues;for(auto p:adjacent){if(p.first==p.second||!std::count(items.begin(),items.end(),p.first)||!std::count(items.begin(),items.end(),p.second))return std::nullopt;if(p.second<p.first)std::swap(p.first,p.second);if(!clues.insert(p).second)return std::nullopt;}std::sort(items.begin(),items.end());std::size_t count=0;do{std::map<std::string,std::size_t> at;for(std::size_t i=0;i<items.size();++i)at[items[i]]=i;bool ok=true;for(auto [s,p]:forced)ok&=at[s]==p;for(auto [a,b]:clues)ok&=std::abs(static_cast<long long>(at[a])-static_cast<long long>(at[b]))==1;count+=ok;}while(std::next_permutation(items.begin(),items.end()));return count;
''',
        r'''
require_case(count_adjacency_placements({"a","b","c"},{{"a",0}},{{"a","b"}})==1);
require_case(count_adjacency_placements({"a","b"}, {},{{"a","b"}})==2);
require_case(count_adjacency_placements({}, {},{})==1);
require_case(!count_adjacency_placements({"a","a"}, {},{}));
require_case(!count_adjacency_placements({"a"}, {},{{"a","a"}}));
''',
        ("at most ten unique named items", "fixed positions and names are unique", "adjacency is unordered", "duplicate clues reject", "the empty permutation counts once"),
        "bounded lexicographic permutation enumeration with indexed predicates", ("zebra", "adjacency", "constraint-count"),
    )
    add(
        "Zebra Puzzle", "latin-row-completion", "Latin row completion",
        "Complete exactly one row of an n by n Latin square over values 1 through n, using zero for blanks. All other rows must be complete, every column must have no duplicate nonzero value, and return the unique completed row or reject ambiguity/impossibility.",
        "", "std::optional<std::vector<int>> complete_unique_latin_row(std::vector<std::vector<int>> grid, std::size_t row)",
        r'''
std::size_t n=grid.size();if(n==0||row>=n)return std::nullopt;for(const auto&r:grid)if(r.size()!=n)return std::nullopt;for(std::size_t r=0;r<n;++r)for(int v:grid[r])if(v<0||v>static_cast<int>(n)||(r!=row&&v==0))return std::nullopt;std::vector<std::vector<int>> solutions;std::function<void(std::size_t)> fill=[&](std::size_t c){if(c==n){for(std::size_t r=0;r<n;++r){std::set<int>s(grid[r].begin(),grid[r].end());if(s.size()!=n||*s.begin()!=1||*s.rbegin()!=static_cast<int>(n))return;}solutions.push_back(grid[row]);return;}if(grid[row][c]){fill(c+1);return;}for(int v=1;v<=static_cast<int>(n);++v){bool ok=true;for(std::size_t k=0;k<n;++k)if(grid[row][k]==v||grid[k][c]==v)ok=false;if(ok){grid[row][c]=v;fill(c+1);grid[row][c]=0;}}};for(std::size_t c=0;c<n;++c){std::set<int>s;for(std::size_t r=0;r<n;++r)if(grid[r][c]&&!s.insert(grid[r][c]).second)return std::nullopt;}fill(0);if(solutions.size()!=1)return std::nullopt;return solutions[0];
''',
        r'''
require_case(complete_unique_latin_row({{1,2},{0,0}},1).value()==std::vector<int>({2,1}));
require_case(complete_unique_latin_row({{1}},0).value()==std::vector<int>{1});
require_case(!complete_unique_latin_row({},0));
require_case(!complete_unique_latin_row({{1,1},{0,0}},1));
require_case(!complete_unique_latin_row({{1,2},{0}},1));
''',
        ("grid is nonempty square", "only target row may contain zero", "values are in range", "rows and columns are Latin", "exactly one completion is required"),
        "bounded row backtracking with full Latin validation", ("zebra", "latin-square", "unique-completion"),
    )
    add(
        "Zebra Puzzle", "minimum-unique-clue-subset", "Minimum unique clue subset",
        "Each of up to twenty clues eliminates a bit mask of candidates from a nonempty candidate universe of at most 63 bits. Choose the lexicographically earliest minimum clue-index set that leaves exactly the target candidate.",
        "", "std::optional<std::vector<std::size_t>> minimum_unique_clue_subset(std::uint64_t candidate_mask, std::size_t target, const std::vector<std::uint64_t>& eliminated_by_clue)",
        r'''
if(candidate_mask==0||target>=63||!(candidate_mask&(std::uint64_t{1}<<target))||eliminated_by_clue.size()>20)return std::nullopt;for(auto m:eliminated_by_clue)if((m&~candidate_mask)||(m&(std::uint64_t{1}<<target)))return std::nullopt;std::vector<std::size_t> best;bool found=false;std::uint64_t limit=std::uint64_t{1}<<eliminated_by_clue.size();for(std::uint64_t bits=0;bits<limit;++bits){std::uint64_t remain=candidate_mask;std::vector<std::size_t> pick;for(std::size_t i=0;i<eliminated_by_clue.size();++i)if(bits&(std::uint64_t{1}<<i)){remain&=~eliminated_by_clue[i];pick.push_back(i);}if(remain==(std::uint64_t{1}<<target)&&(!found||pick.size()<best.size()||(pick.size()==best.size()&&pick<best))){best=pick;found=true;}}if(!found)return std::vector<std::size_t>{};return best;
''',
        r'''
require_case(minimum_unique_clue_subset(7,0,{2,4,6}).value()==std::vector<std::size_t>{2});
require_case(minimum_unique_clue_subset(1,0,{}).value().empty());
require_case(minimum_unique_clue_subset(3,0,{}).value().empty());
require_case(!minimum_unique_clue_subset(0,0,{}));
require_case(!minimum_unique_clue_subset(3,0,{1}));
''',
        ("candidate universe is nonempty and within 63 bits", "target is present", "at most twenty clues", "clues only eliminate non-target candidates", "empty inner vector is also the no-solution sentinel"),
        "bounded clue-subset enumeration with canonical minimum witness", ("zebra", "clue-minimization", "set-cover"),
    )

    return specs
