#!/usr/bin/env python3
"""Clean-room CHARM V1 task specifications for the v1q86 lineage."""

from __future__ import annotations

import re


def build_specs(Spec):
    specs = []

    def add(topic, slug, title, contract, types, signature, body, tests, strategy, tags):
        topic_ns = re.sub(r"[^a-z0-9]+", "_", topic.casefold()).strip("_")
        namespace = f"charm::v1q86::{topic_ns}"
        definition = f"namespace {namespace} {{\n{signature} {{ {body} }}\n}}"
        test_source = f"using namespace {namespace};\nint main() {{ {tests} return 0; }}"
        edges = (
            "malformed domains reject before producing partial output",
            "empty input has an explicit deterministic interpretation",
            "ordering and tie behavior are part of the contract",
            "arithmetic and indices are checked before use",
            "the result is canonical across equivalent inputs",
        )
        specs.append(Spec(
            topic, slug, title, contract, types, signature, definition,
            test_source, edges, strategy, tuple(tags),
        ))

    add(
        "Allergies", "dose-concurrency-profile", "Dose concurrency profile",
        "Sweep labeled half-open exposure intervals and report the maximum simultaneous exposure count and the earliest minute at which that maximum begins. Labels must be nonempty, intervals nonempty, and exact duplicate intervals reject.",
        "struct DoseSpan { int begin; int end; std::string label; };\nstruct ExposurePeak { int count; int first_minute; };",
        "std::optional<ExposurePeak> dose_concurrency_profile(const std::vector<DoseSpan>& spans)",
        "std::set<std::tuple<int,int,std::string>> unique;std::map<int,int> delta;for(const auto&s:spans){if(s.label.empty()||s.begin<0||s.begin>=s.end||!unique.emplace(s.begin,s.end,s.label).second)return std::nullopt;++delta[s.begin];--delta[s.end];}ExposurePeak out{0,0};int active=0;for(const auto&item:delta){active+=item.second;if(active>out.count)out={active,item.first};}return out;",
        "auto r=dose_concurrency_profile({{1,5,\"a\"},{3,7,\"b\"},{3,4,\"c\"}});require_case(r&&r->count==3&&r->first_minute==3);require_case(dose_concurrency_profile({})->count==0);require_case(!dose_concurrency_profile({{2,2,\"x\"}}));require_case(!dose_concurrency_profile({{1,2,\"x\"},{1,2,\"x\"}}));",
        "ordered endpoint sweep with end-before-start half-open accounting", ("exposure", "sweep", "peak"),
    )
    add(
        "Allergies", "panel-vote-consensus", "Panel vote consensus",
        "Select allergens receiving at least a requested number of independent panel votes over a declared sorted universe. Every ballot is sorted unique and must be a subset of the universe.",
        "",
        "std::optional<std::vector<std::string>> panel_vote_consensus(const std::vector<std::string>& universe, const std::vector<std::vector<std::string>>& ballots, std::size_t required_votes)",
        "if(!std::is_sorted(universe.begin(),universe.end())||std::adjacent_find(universe.begin(),universe.end())!=universe.end()||std::find(universe.begin(),universe.end(),\"\")!=universe.end()||required_votes>ballots.size())return std::nullopt;std::map<std::string,std::size_t> counts;for(const auto&b:ballots){if(!std::is_sorted(b.begin(),b.end())||std::adjacent_find(b.begin(),b.end())!=b.end())return std::nullopt;for(const auto&x:b)if(!std::binary_search(universe.begin(),universe.end(),x))return std::nullopt;else ++counts[x];}std::vector<std::string> out;for(const auto&x:universe)if(counts[x]>=required_votes)out.push_back(x);return out;",
        "auto r=panel_vote_consensus({\"egg\",\"milk\",\"nut\"},{{\"egg\",\"nut\"},{\"egg\"},{\"milk\",\"nut\"}},2);require_case(r&&*r==std::vector<std::string>({\"egg\",\"nut\"}));require_case(panel_vote_consensus({}, {},0)->empty());require_case(!panel_vote_consensus({\"b\",\"a\"},{},0));require_case(!panel_vote_consensus({\"a\"},{{\"x\"}},1));",
        "validated ballot accumulation followed by universe-order projection", ("panel", "consensus", "votes"),
    )
    add(
        "Allergies", "recipe-risk-frontier", "Recipe risk frontier",
        "Return recipe names whose distinct risky-ingredient count is no greater than a limit. Recipe names and ingredient lists are canonical, and the risky ingredient domain is sorted unique.",
        "struct RecipeCard { std::string name; std::vector<std::string> ingredients; };",
        "std::optional<std::vector<std::string>> recipe_risk_frontier(const std::vector<RecipeCard>& recipes, const std::vector<std::string>& risky, std::size_t maximum_risky)",
        "if(!std::is_sorted(risky.begin(),risky.end())||std::adjacent_find(risky.begin(),risky.end())!=risky.end())return std::nullopt;std::set<std::string> names;std::vector<std::string> out;for(const auto&r:recipes){if(r.name.empty()||!names.insert(r.name).second||!std::is_sorted(r.ingredients.begin(),r.ingredients.end())||std::adjacent_find(r.ingredients.begin(),r.ingredients.end())!=r.ingredients.end())return std::nullopt;std::size_t count=0;for(const auto&i:r.ingredients)count+=std::binary_search(risky.begin(),risky.end(),i);if(count<=maximum_risky)out.push_back(r.name);}std::sort(out.begin(),out.end());return out;",
        "auto r=recipe_risk_frontier({{\"soup\",{\"egg\",\"rice\"}},{\"tea\",{\"water\"}}},{\"egg\",\"nut\"},0);require_case(r&&*r==std::vector<std::string>({\"tea\"}));require_case(recipe_risk_frontier({}, {},3)->empty());require_case(!recipe_risk_frontier({{\"x\",{\"b\",\"a\"}}},{},0));",
        "per-recipe sorted intersection counting with canonical name output", ("recipe", "risk", "frontier"),
    )

    add(
        "Bank Account", "ledger-reversal-pairs", "Ledger reversal pairs",
        "Pair later entries with the earliest unmatched earlier entry carrying the exact opposite nonzero amount. Return identifier pairs in closing-entry order and reject duplicate identifiers or the minimum signed amount.",
        "struct LedgerEntry { std::string id; long long cents; };",
        "std::optional<std::vector<std::pair<std::string,std::string>>> ledger_reversal_pairs(const std::vector<LedgerEntry>& entries)",
        "std::set<std::string> ids;std::map<long long,std::deque<std::string>> waiting;std::vector<std::pair<std::string,std::string>> out;for(const auto&e:entries){if(e.id.empty()||e.cents==0||e.cents==LLONG_MIN||!ids.insert(e.id).second)return std::nullopt;auto&opposite=waiting[-e.cents];if(!opposite.empty()){out.push_back({opposite.front(),e.id});opposite.pop_front();}else waiting[e.cents].push_back(e.id);}return out;",
        "auto r=ledger_reversal_pairs({{\"a\",5},{\"b\",7},{\"c\",-5},{\"d\",-7}});require_case(r&&*r==std::vector<std::pair<std::string,std::string>>({{\"a\",\"c\"},{\"b\",\"d\"}}));require_case(ledger_reversal_pairs({})->empty());require_case(!ledger_reversal_pairs({{\"x\",0}}));",
        "amount-indexed FIFO matching of opposite signed entries", ("ledger", "reversal", "fifo"),
    )
    add(
        "Bank Account", "balanced-settlement-plan", "Balanced settlement plan",
        "Convert sorted unique named net balances summing to zero into a deterministic sequence of debtor-to-creditor transfers. Debtors and creditors are consumed lexicographically and arithmetic is checked.",
        "struct NetBalance { std::string name; long long cents; };\nstruct Transfer { std::string from; std::string to; long long cents; };",
        "std::optional<std::vector<Transfer>> balanced_settlement_plan(const std::vector<NetBalance>& balances)",
        "if(!std::is_sorted(balances.begin(),balances.end(),[](const auto&a,const auto&b){return a.name<b.name;}))return std::nullopt;std::vector<NetBalance> debt,credit;long long total=0;for(const auto&b:balances){if(b.name.empty()||(b.cents>0&&total>LLONG_MAX-b.cents)||(b.cents<0&&total<LLONG_MIN-b.cents))return std::nullopt;total+=b.cents;if(b.cents<0)debt.push_back({b.name,-b.cents});else if(b.cents>0)credit.push_back(b);}if(total!=0)return std::nullopt;std::vector<Transfer> out;std::size_t i=0,j=0;while(i<debt.size()&&j<credit.size()){long long x=std::min(debt[i].cents,credit[j].cents);out.push_back({debt[i].name,credit[j].name,x});debt[i].cents-=x;credit[j].cents-=x;if(debt[i].cents==0)++i;if(credit[j].cents==0)++j;}return out;",
        "auto r=balanced_settlement_plan({{\"a\",-5},{\"b\",-2},{\"c\",7}});require_case(r&&r->size()==2&&r->at(0).from==\"a\"&&r->at(1).cents==2);require_case(balanced_settlement_plan({})->empty());require_case(!balanced_settlement_plan({{\"a\",1}}));",
        "two-frontier lexicographic debtor-creditor cancellation", ("settlement", "balances", "transfers"),
    )
    add(
        "Bank Account", "balance-drawdown-profile", "Balance drawdown profile",
        "Apply signed deltas to an opening balance and return the closing balance, minimum observed balance, and first one-based entry reaching that minimum. Every addition is overflow checked.",
        "struct DrawdownProfile { long long closing; long long minimum; std::size_t first_minimum_entry; };",
        "std::optional<DrawdownProfile> balance_drawdown_profile(long long opening, const std::vector<long long>& deltas)",
        "DrawdownProfile out{opening,opening,0};long long value=opening;for(std::size_t i=0;i<deltas.size();++i){long long d=deltas[i];if((d>0&&value>LLONG_MAX-d)||(d<0&&value<LLONG_MIN-d))return std::nullopt;value+=d;if(value<out.minimum){out.minimum=value;out.first_minimum_entry=i+1;}}out.closing=value;return out;",
        "auto r=balance_drawdown_profile(10,{-3,-9,4});require_case(r&&r->closing==2&&r->minimum==-2&&r->first_minimum_entry==2);require_case(balance_drawdown_profile(4,{})->minimum==4);require_case(!balance_drawdown_profile(LLONG_MAX,{1}));",
        "single-pass checked prefix minimum with stable first-index tie", ("drawdown", "prefix", "overflow"),
    )

    add(
        "Binary Search Tree", "inorder-gap-certificate", "Inorder gap certificate",
        "Validate a fully reachable indexed strict binary-search tree and return positive adjacent-key gaps from its inorder traversal. Cycles, sharing, invalid children, unreachable nodes, and subtraction overflow reject.",
        "struct GapNode { long long key; int left; int right; };",
        "std::optional<std::vector<unsigned long long>> inorder_gap_certificate(const std::vector<GapNode>& nodes, int root)",
        "if(nodes.empty())return root==-1?std::optional<std::vector<unsigned long long>>{{}}:std::nullopt;if(root<0||root>=static_cast<int>(nodes.size()))return std::nullopt;std::vector<int> state(nodes.size());std::vector<long long> keys;std::function<bool(int,long long,long long)> walk=[&](int x,long long lo,long long hi){if(x==-1)return true;if(x<0||x>=static_cast<int>(nodes.size())||state[x]||nodes[x].key<=lo||nodes[x].key>=hi)return false;state[x]=1;if(!walk(nodes[x].left,lo,nodes[x].key))return false;keys.push_back(nodes[x].key);if(!walk(nodes[x].right,nodes[x].key,hi))return false;state[x]=2;return true;};if(!walk(root,LLONG_MIN,LLONG_MAX)||std::find(state.begin(),state.end(),0)!=state.end())return std::nullopt;std::vector<unsigned long long> out;for(std::size_t i=1;i<keys.size();++i)out.push_back(static_cast<unsigned long long>(keys[i])-static_cast<unsigned long long>(keys[i-1]));return out;",
        "auto r=inorder_gap_certificate({{4,1,2},{1,-1,-1},{9,-1,-1}},0);require_case(r&&*r==std::vector<unsigned long long>({3,5}));require_case(inorder_gap_certificate({},-1)->empty());require_case(!inorder_gap_certificate({{1,0,-1}},0));",
        "range-bounded recursive validation coupled to inorder gap emission", ("bst", "inorder", "gaps"),
    )
    add(
        "Binary Search Tree", "query-path-turn-counts", "Query path turn counts",
        "For node-pair queries in a rooted indexed binary tree, count direction changes along the unique path between endpoints. The entire tree must be reachable exactly once and queries preserve input order.",
        "struct TurnNode { int left; int right; };\nstruct TurnQuery { int first; int second; };",
        "std::optional<std::vector<std::size_t>> query_path_turn_counts(const std::vector<TurnNode>& nodes, int root, const std::vector<TurnQuery>& queries)",
        "if(nodes.empty())return root==-1&&queries.empty()?std::optional<std::vector<std::size_t>>{{}}:std::nullopt;if(root<0||root>=static_cast<int>(nodes.size()))return std::nullopt;std::vector<int> parent(nodes.size(),-2),side(nodes.size());parent[root]=-1;std::queue<int> q;q.push(root);while(!q.empty()){int x=q.front();q.pop();for(auto edge:std::array<std::pair<int,int>,2>{{{nodes[x].left,-1},{nodes[x].right,1}}})if(edge.first!=-1){if(edge.first<0||edge.first>=static_cast<int>(nodes.size())||parent[edge.first]!=-2)return std::nullopt;parent[edge.first]=x;side[edge.first]=edge.second;q.push(edge.first);}}if(std::find(parent.begin(),parent.end(),-2)!=parent.end())return std::nullopt;std::vector<std::size_t> out;for(auto query:queries){if(query.first<0||query.second<0||query.first>=static_cast<int>(nodes.size())||query.second>=static_cast<int>(nodes.size()))return std::nullopt;std::vector<int>a,b;for(int x=query.first;x!=root;x=parent[x])a.push_back(side[x]);for(int x=query.second;x!=root;x=parent[x])b.push_back(-side[x]);std::reverse(b.begin(),b.end());a.insert(a.end(),b.begin(),b.end());std::size_t turns=0;for(std::size_t i=1;i<a.size();++i)turns+=a[i]!=a[i-1];out.push_back(turns);}return out;",
        "auto r=query_path_turn_counts({{1,2},{3,-1},{-1,-1},{-1,-1}},0,{{3,2},{1,3}});require_case(r&&r->at(0)==2&&r->at(1)==0);require_case(query_path_turn_counts({{-1,-1}},0,{{0,0}})->at(0)==0);require_case(!query_path_turn_counts({{1,1},{-1,-1}},0,{}));",
        "parent/side indexing followed by endpoint path-word turn counting", ("tree", "path", "turns"),
    )
    add(
        "Binary Search Tree", "subtree-level-checksums", "Subtree level checksums",
        "For every node of a fully reachable indexed tree, compute a deterministic checksum of keys in that node's subtree grouped by relative depth. Return one checksum vector per node.",
        "struct CheckNode { int key; int left; int right; };",
        "std::optional<std::vector<std::vector<long long>>> subtree_level_checksums(const std::vector<CheckNode>& nodes, int root)",
        "if(nodes.empty())return root==-1?std::optional<std::vector<std::vector<long long>>>{{}}:std::nullopt;if(root<0||root>=static_cast<int>(nodes.size()))return std::nullopt;std::vector<int> seen(nodes.size());std::function<std::optional<std::vector<long long>>(int)> rec=[&](int x)->std::optional<std::vector<long long>>{if(x==-1)return std::vector<long long>{};if(x<0||x>=static_cast<int>(nodes.size())||seen[x]++)return std::nullopt;auto a=rec(nodes[x].left),b=rec(nodes[x].right);if(!a||!b)return std::nullopt;std::vector<long long> v(std::max(a->size(),b->size())+1);v[0]=nodes[x].key;for(std::size_t i=0;i<a->size();++i)v[i+1]+=a->at(i);for(std::size_t i=0;i<b->size();++i)v[i+1]+=b->at(i);return v;};std::vector<std::vector<long long>> out(nodes.size());for(std::size_t i=0;i<nodes.size();++i){std::fill(seen.begin(),seen.end(),0);auto v=rec(static_cast<int>(i));if(!v)return std::nullopt;out[i]=*v;}std::fill(seen.begin(),seen.end(),0);if(!rec(root)||std::find(seen.begin(),seen.end(),0)!=seen.end())return std::nullopt;return out;",
        "auto r=subtree_level_checksums({{1,1,2},{2,-1,-1},{3,-1,-1}},0);require_case(r&&r->at(0)==std::vector<long long>({1,5})&&r->at(1)==std::vector<long long>({2}));require_case(subtree_level_checksums({},-1)->empty());require_case(!subtree_level_checksums({{1,0,-1}},0));",
        "memo-free per-root depth aggregation plus whole-tree reachability proof", ("subtree", "levels", "checksum"),
    )

    add(
        "Circular Buffer", "ring-resize-replay", "Ring resize replay",
        "Replay push, pop, and capacity-change commands over a FIFO ring. Shrinking below the current size rejects, pop records removed values, and zero capacity is valid only for an empty ring.",
        "struct RingCommand { char kind; int value; };\nstruct RingReplay { std::vector<int> remaining; std::vector<int> popped; };",
        "std::optional<RingReplay> ring_resize_replay(std::size_t initial_capacity, const std::vector<RingCommand>& commands)",
        "std::deque<int> ring;std::size_t capacity=initial_capacity;RingReplay out;for(auto c:commands){if(c.kind=='P'){if(ring.size()==capacity)return std::nullopt;ring.push_back(c.value);}else if(c.kind=='O'){if(c.value!=0||ring.empty())return std::nullopt;out.popped.push_back(ring.front());ring.pop_front();}else if(c.kind=='R'){if(c.value<0||static_cast<std::size_t>(c.value)<ring.size())return std::nullopt;capacity=static_cast<std::size_t>(c.value);}else return std::nullopt;}out.remaining.assign(ring.begin(),ring.end());return out;",
        "auto r=ring_resize_replay(2,{{'P',1},{'P',2},{'O',0},{'R',3},{'P',4}});require_case(r&&r->remaining==std::vector<int>({2,4})&&r->popped==std::vector<int>({1}));require_case(ring_resize_replay(0,{})->remaining.empty());require_case(!ring_resize_replay(0,{{'P',1}}));",
        "capacity-aware deque command machine with explicit pop transcript", ("ring", "resize", "replay"),
    )
    add(
        "Circular Buffer", "cyclic-run-canonicalization", "Cyclic run canonicalization",
        "Compress equal-value runs on a nonempty ring, merging the first and last linear runs when their values agree. Rotate the run list so the lexicographically smallest value/count pair is first.",
        "struct ValueRun { int value; std::size_t count; };",
        "std::optional<std::vector<ValueRun>> cyclic_run_canonicalization(const std::vector<int>& ring)",
        "if(ring.empty())return std::nullopt;std::vector<ValueRun> runs;for(int x:ring){if(runs.empty()||runs.back().value!=x)runs.push_back({x,1});else ++runs.back().count;}if(runs.size()>1&&runs.front().value==runs.back().value){runs.front().count+=runs.back().count;runs.pop_back();}auto it=std::min_element(runs.begin(),runs.end(),[](const auto&a,const auto&b){return std::tie(a.value,a.count)<std::tie(b.value,b.count);});std::rotate(runs.begin(),it,runs.end());return runs;",
        "auto r=cyclic_run_canonicalization({1,1,2,3,1});require_case(r&&r->size()==3&&r->front().value==1&&r->front().count==3);require_case(cyclic_run_canonicalization({7})->front().count==1);require_case(!cyclic_run_canonicalization({}));",
        "linear run compression, boundary fusion, and canonical rotation", ("cyclic", "runs", "canonical"),
    )
    add(
        "Circular Buffer", "ring-window-distinct-profile", "Ring window distinct profile",
        "Count distinct integers in every fixed-length cyclic window beginning at each ring index. Window length is positive and no greater than ring size.",
        "",
        "std::optional<std::vector<std::size_t>> ring_window_distinct_profile(const std::vector<int>& ring, std::size_t window)",
        "if(ring.empty()||window==0||window>ring.size())return std::nullopt;std::map<int,std::size_t> counts;for(std::size_t i=0;i<window;++i)++counts[ring[i]];std::vector<std::size_t> out;for(std::size_t start=0;start<ring.size();++start){out.push_back(counts.size());int leaving=ring[start],entering=ring[(start+window)%ring.size()];if(--counts[leaving]==0)counts.erase(leaving);++counts[entering];}return out;",
        "auto r=ring_window_distinct_profile({1,2,1,3},3);require_case(r&&*r==std::vector<std::size_t>({2,3,2,3}));require_case(ring_window_distinct_profile({5},1)->at(0)==1);require_case(!ring_window_distinct_profile({},1));",
        "sliding cyclic frequency map with constant-window updates", ("ring", "window", "distinct"),
    )

    add(
        "Clock", "timezone-overlap-segments", "Timezone overlap segments",
        "Convert local half-open availability windows using signed minute offsets, clip them to one UTC day, and return maximal intervals where at least a threshold number of calendars overlap.",
        "struct LocalWindow { int begin; int end; int utc_offset; };\nstruct MinuteSegment { int begin; int end; };",
        "std::optional<std::vector<MinuteSegment>> timezone_overlap_segments(const std::vector<LocalWindow>& windows, std::size_t threshold)",
        "if(threshold==0)return std::nullopt;std::map<int,int> delta;for(auto w:windows){if(w.begin<0||w.begin>=w.end||w.end>1440||w.utc_offset<-840||w.utc_offset>840)return std::nullopt;int a=std::max(0,w.begin-w.utc_offset),b=std::min(1440,w.end-w.utc_offset);if(a<b){++delta[a];--delta[b];}}std::vector<MinuteSegment> out;int active=0,start=-1;for(auto point:delta){int before=active;active+=point.second;if(before<static_cast<int>(threshold)&&active>=static_cast<int>(threshold))start=point.first;if(before>=static_cast<int>(threshold)&&active<static_cast<int>(threshold)){out.push_back({start,point.first});start=-1;}}return out;",
        "auto r=timezone_overlap_segments({{60,180,60},{30,150,0}},2);require_case(r&&r->size()==1&&r->front().begin==30&&r->front().end==120);require_case(timezone_overlap_segments({},1)->empty());require_case(!timezone_overlap_segments({},0));",
        "offset conversion and thresholded UTC endpoint sweep", ("timezone", "overlap", "segments"),
    )
    add(
        "Clock", "chime-coincidence-count", "Chime coincidence count",
        "Count timestamps in an inclusive horizon where every periodic chime rings. Each chime has a positive period and an offset in its canonical residue range; arithmetic must remain bounded.",
        "struct Chime { int period; int offset; };",
        "std::optional<std::uint64_t> chime_coincidence_count(const std::vector<Chime>& chimes, int horizon)",
        "if(horizon<0)return std::nullopt;for(auto c:chimes)if(c.period<=0||c.offset<0||c.offset>=c.period)return std::nullopt;std::uint64_t count=0;for(int t=0;t<=horizon;++t){bool all=true;for(auto c:chimes)all=all&&t%c.period==c.offset;if(all)++count;}return count;",
        "require_case(chime_coincidence_count({{3,1},{4,1}},20)==2);require_case(chime_coincidence_count({},5)==6);require_case(!chime_coincidence_count({{0,0}},5));require_case(!chime_coincidence_count({},-1));",
        "bounded horizon enumeration with simultaneous modular predicates", ("clock", "chime", "modular"),
    )
    add(
        "Clock", "signed-time-carry-normalizer", "Signed time carry normalizer",
        "Normalize a signed day/hour/minute/second tuple into a floor-based day plus nonnegative within-day fields. Detect accumulation overflow before normalization.",
        "struct TimeCarry { long long day; int hour; int minute; int second; };",
        "std::optional<TimeCarry> signed_time_carry_normalizer(long long day, long long hour, long long minute, long long second)",
        "if(day>LLONG_MAX/86400||day<LLONG_MIN/86400)return std::nullopt;long long total=day*86400;auto add=[&](long long x){if((x>0&&total>LLONG_MAX-x)||(x<0&&total<LLONG_MIN-x))return false;total+=x;return true;};if(hour>LLONG_MAX/3600||hour<LLONG_MIN/3600||minute>LLONG_MAX/60||minute<LLONG_MIN/60||!add(hour*3600)||!add(minute*60)||!add(second))return std::nullopt;long long d=total/86400,rem=total%86400;if(rem<0){rem+=86400;--d;}return TimeCarry{d,static_cast<int>(rem/3600),static_cast<int>(rem/60%60),static_cast<int>(rem%60)};",
        "auto r=signed_time_carry_normalizer(0,0,0,-1);require_case(r&&r->day==-1&&r->hour==23&&r->minute==59&&r->second==59);require_case(signed_time_carry_normalizer(1,25,0,0)->day==2);require_case(!signed_time_carry_normalizer(LLONG_MAX,0,0,0));",
        "checked scalar accumulation followed by Euclidean day decomposition", ("time", "carry", "normalize"),
    )

    add(
        "Complex Numbers", "complex-polyline-energy", "Complex polyline energy",
        "Compute the sum of squared Euclidean lengths of consecutive complex samples and the index of the longest segment, with the earliest segment breaking ties. Inputs must be finite.",
        "struct PolylineEnergy { double total; std::size_t longest_segment; };",
        "std::optional<PolylineEnergy> complex_polyline_energy(const std::vector<std::complex<double>>& samples)",
        "for(auto z:samples)if(!std::isfinite(z.real())||!std::isfinite(z.imag()))return std::nullopt;PolylineEnergy out{0.0,0};double longest=-1.0;for(std::size_t i=1;i<samples.size();++i){double value=std::norm(samples[i]-samples[i-1]);if(!std::isfinite(value)||!std::isfinite(out.total+value))return std::nullopt;out.total+=value;if(value>longest){longest=value;out.longest_segment=i-1;}}return out;",
        "auto r=complex_polyline_energy({{0,0},{3,4},{3,5}});require_case(r&&std::abs(r->total-26.0)<1e-12&&r->longest_segment==0);require_case(complex_polyline_energy({})->total==0.0);require_case(!complex_polyline_energy({{INFINITY,0}}));",
        "finite segment-norm accumulation with stable argmax", ("complex", "polyline", "energy"),
    )
    add(
        "Complex Numbers", "mobius-transform-batch", "Mobius transform batch",
        "Apply one complex Mobius transform to a sample batch, rejecting a degenerate transform or any denominator whose magnitude is at most epsilon. Preserve sample order.",
        "struct Mobius { std::complex<double> a; std::complex<double> b; std::complex<double> c; std::complex<double> d; };",
        "std::optional<std::vector<std::complex<double>>> mobius_transform_batch(const Mobius& transform, const std::vector<std::complex<double>>& samples, double epsilon)",
        "if(!(epsilon>=0.0)||std::norm(transform.a*transform.d-transform.b*transform.c)<=epsilon*epsilon)return std::nullopt;std::vector<std::complex<double>> out;for(auto z:samples){auto denominator=transform.c*z+transform.d;if(std::norm(denominator)<=epsilon*epsilon)return std::nullopt;auto value=(transform.a*z+transform.b)/denominator;if(!std::isfinite(value.real())||!std::isfinite(value.imag()))return std::nullopt;out.push_back(value);}return out;",
        "auto r=mobius_transform_batch({{1,0},{1,0},{0,0},{1,0}},{{2,0}},1e-9);require_case(r&&std::abs(r->front().real()-3.0)<1e-12);require_case(mobius_transform_batch({{1,0},{0,0},{0,0},{1,0}}, {},0)->empty());require_case(!mobius_transform_batch({{1,0},{0,0},{0,0},{0,0}},{{1,0}},0));",
        "determinant validation and guarded pointwise fractional transform", ("complex", "mobius", "batch"),
    )
    add(
        "Complex Numbers", "phasor-quadrant-occupancy", "Phasor quadrant occupancy",
        "Classify non-axis complex samples into four open quadrants and count samples lying on either axis within epsilon separately. Reject non-finite samples and invalid epsilon.",
        "struct QuadrantOccupancy { std::array<std::size_t,4> quadrants; std::size_t on_axis; };",
        "std::optional<QuadrantOccupancy> phasor_quadrant_occupancy(const std::vector<std::complex<double>>& samples, double epsilon)",
        "if(!(epsilon>=0.0))return std::nullopt;QuadrantOccupancy out{};for(auto z:samples){double x=z.real(),y=z.imag();if(!std::isfinite(x)||!std::isfinite(y))return std::nullopt;if(std::abs(x)<=epsilon||std::abs(y)<=epsilon){++out.on_axis;continue;}std::size_t index=y>0?(x>0?0:1):(x<0?2:3);++out.quadrants[index];}return out;",
        "auto r=phasor_quadrant_occupancy({{1,1},{-1,1},{-1,-1},{1,-1},{0,2}},0);require_case(r&&r->quadrants==std::array<std::size_t,4>({1,1,1,1})&&r->on_axis==1);require_case(phasor_quadrant_occupancy({},0)->on_axis==0);require_case(!phasor_quadrant_occupancy({},-1));",
        "epsilon-axis partition with explicit quadrant indexing", ("phasor", "quadrant", "occupancy"),
    )

    add(
        "Crypto Square", "rotating-grille-orbits", "Rotating grille orbits",
        "Validate holes in an odd square rotating grille and return their four-position rotation orbits in canonical order. The center is forbidden and no two holes may share an orbit.",
        "struct GridCell { int row; int column; };",
        "std::optional<std::vector<std::array<GridCell,4>>> rotating_grille_orbits(int side, const std::vector<GridCell>& holes)",
        "if(side<=0||side%2==0)return std::nullopt;std::set<std::pair<int,int>> occupied;std::vector<std::array<GridCell,4>> out;for(auto h:holes){if(h.row<0||h.column<0||h.row>=side||h.column>=side||(h.row==side/2&&h.column==side/2))return std::nullopt;std::array<GridCell,4> orbit{};for(int i=0;i<4;++i){orbit[i]=h;if(!occupied.emplace(h.row,h.column).second)return std::nullopt;h={h.column,side-1-h.row};}out.push_back(orbit);}std::sort(out.begin(),out.end(),[](const auto&a,const auto&b){return std::tie(a[0].row,a[0].column)<std::tie(b[0].row,b[0].column);});return out;",
        "auto r=rotating_grille_orbits(3,{{0,0},{0,1}});require_case(r&&r->size()==2&&r->front()[2].row==2);require_case(rotating_grille_orbits(1,{})->empty());require_case(!rotating_grille_orbits(3,{{0,0},{2,2}}));",
        "fourfold coordinate orbit expansion with global occupancy proof", ("grille", "rotation", "orbits"),
    )
    add(
        "Crypto Square", "xor-block-parity-map", "XOR block parity map",
        "Split bytes into fixed-size blocks, XOR each block, and return indices whose XOR has odd population parity. The final partial block participates and block size must be positive.",
        "",
        "std::optional<std::vector<std::size_t>> xor_block_parity_map(const std::vector<unsigned char>& bytes, std::size_t block_size)",
        "if(block_size==0)return std::nullopt;std::vector<std::size_t> out;for(std::size_t begin=0,index=0;begin<bytes.size();begin+=block_size,++index){unsigned char x=0;for(std::size_t i=begin;i<std::min(bytes.size(),begin+block_size);++i)x^=bytes[i];unsigned bits=0;for(unsigned char y=x;y;y>>=1)bits+=y&1U;if(bits%2)out.push_back(index);}return out;",
        "auto r=xor_block_parity_map({1,2,3,7},2);require_case(r&&*r==std::vector<std::size_t>({1}));require_case(xor_block_parity_map({},4)->empty());require_case(xor_block_parity_map({1},8)->at(0)==0);require_case(!xor_block_parity_map({},0));",
        "blockwise XOR reduction followed by explicit bit-parity extraction", ("xor", "blocks", "parity"),
    )
    add(
        "Crypto Square", "permutation-cycle-schedule", "Permutation cycle schedule",
        "Decompose a zero-based permutation into cycles, rotating each cycle to its minimum element and sorting cycles by that element. Invalid, repeated, or missing targets reject.",
        "",
        "std::optional<std::vector<std::vector<std::size_t>>> permutation_cycle_schedule(const std::vector<std::size_t>& permutation)",
        "std::vector<unsigned char> seen(permutation.size());for(auto x:permutation)if(x>=permutation.size()||seen[x]++)return std::nullopt;std::fill(seen.begin(),seen.end(),0);std::vector<std::vector<std::size_t>> out;for(std::size_t start=0;start<permutation.size();++start)if(!seen[start]){std::vector<std::size_t> cycle;for(std::size_t x=start;!seen[x];x=permutation[x]){seen[x]=1;cycle.push_back(x);}auto minimum=std::min_element(cycle.begin(),cycle.end());std::rotate(cycle.begin(),minimum,cycle.end());out.push_back(cycle);}std::sort(out.begin(),out.end());return out;",
        "auto r=permutation_cycle_schedule({2,0,1,4,3});require_case(r&&*r==std::vector<std::vector<std::size_t>>({{0,2,1},{3,4}}));require_case(permutation_cycle_schedule({})->empty());require_case(!permutation_cycle_schedule({1,1}));",
        "visited permutation traversal with minimum-rooted cycle canonicalization", ("permutation", "cycles", "schedule"),
    )

    add(
        "Diamond", "diamond-ring-sector-sums", "Diamond ring sector sums",
        "For lattice points on one Manhattan ring, sum values in the four directed sectors beginning at north and proceeding clockwise. Axis boundary ownership is fixed and duplicate coordinates reject.",
        "struct WeightedPoint { int x; int y; long long value; };",
        "std::optional<std::array<long long,4>> diamond_ring_sector_sums(int radius, const std::vector<WeightedPoint>& points)",
        "if(radius<=0)return std::nullopt;std::set<std::pair<int,int>> seen;std::array<long long,4> out{};for(auto p:points){if(std::abs(p.x)+std::abs(p.y)!=radius||!seen.emplace(p.x,p.y).second)return std::nullopt;std::size_t sector=p.y>0&&p.x>=0?0:p.x>0&&p.y<=0?1:p.y<0&&p.x<=0?2:3;if((p.value>0&&out[sector]>LLONG_MAX-p.value)||(p.value<0&&out[sector]<LLONG_MIN-p.value))return std::nullopt;out[sector]+=p.value;}return out;",
        "auto r=diamond_ring_sector_sums(2,{{0,2,1},{2,0,2},{0,-2,3},{-2,0,4}});require_case(r&&*r==std::array<long long,4>({1,2,3,4}));require_case(diamond_ring_sector_sums(1,{})->at(0)==0);require_case(!diamond_ring_sector_sums(0,{}));",
        "axis-owned sector classification with checked accumulation", ("diamond", "sectors", "sums"),
    )
    add(
        "Diamond", "manhattan-shell-histogram", "Manhattan shell histogram",
        "Count points by Manhattan distance from a signed center up to an inclusive maximum radius. Coordinate subtraction and absolute-value conversion are checked.",
        "struct LatticePoint { long long x; long long y; };",
        "std::optional<std::vector<std::size_t>> manhattan_shell_histogram(LatticePoint center, const std::vector<LatticePoint>& points, std::size_t maximum_radius)",
        "std::vector<std::size_t> out(maximum_radius+1);for(auto p:points){if((p.x<center.x&&center.x-p.x<0)||(p.y<center.y&&center.y-p.y<0))return std::nullopt;unsigned long long dx=p.x>=center.x?static_cast<unsigned long long>(p.x)-static_cast<unsigned long long>(center.x):static_cast<unsigned long long>(center.x)-static_cast<unsigned long long>(p.x);unsigned long long dy=p.y>=center.y?static_cast<unsigned long long>(p.y)-static_cast<unsigned long long>(center.y):static_cast<unsigned long long>(center.y)-static_cast<unsigned long long>(p.y);if(dx>maximum_radius||dy>maximum_radius-dx)return std::nullopt;++out[static_cast<std::size_t>(dx+dy)];}return out;",
        "auto r=manhattan_shell_histogram({0,0},{{0,0},{1,0},{-1,1}},2);require_case(r&&*r==std::vector<std::size_t>({1,1,1}));require_case(manhattan_shell_histogram({5,5},{},0)->at(0)==0);require_case(!manhattan_shell_histogram({0,0},{{3,0}},2));",
        "checked unsigned coordinate deltas into bounded shell buckets", ("manhattan", "shell", "histogram"),
    )
    add(
        "Diamond", "diamond-ray-hit-counts", "Diamond ray hit counts",
        "Cast four diagonal rays from a center and count declared points lying strictly on each ray within a maximum step. Points on no ray are ignored; duplicates and nonpositive limits reject.",
        "struct RayPoint { int x; int y; };",
        "std::optional<std::array<std::size_t,4>> diamond_ray_hit_counts(RayPoint center, const std::vector<RayPoint>& points, int maximum_step)",
        "if(maximum_step<=0)return std::nullopt;std::set<std::pair<int,int>> unique;std::array<std::size_t,4> out{};for(auto p:points){if(!unique.emplace(p.x,p.y).second)return std::nullopt;long long dx=static_cast<long long>(p.x)-center.x,dy=static_cast<long long>(p.y)-center.y;if(dx==0||std::llabs(dx)!=std::llabs(dy)||std::llabs(dx)>maximum_step)continue;std::size_t index=dy<0?(dx>0?0:3):(dx>0?1:2);++out[index];}return out;",
        "auto r=diamond_ray_hit_counts({0,0},{{1,-1},{2,2},{-1,1},{-2,-2},{1,0}},3);require_case(r&&*r==std::array<std::size_t,4>({1,1,1,1}));require_case(diamond_ray_hit_counts({0,0},{},1)->at(0)==0);require_case(!diamond_ray_hit_counts({0,0},{},0));",
        "signed diagonal-ray classification with bounded step filtering", ("diamond", "rays", "hits"),
    )

    add(
        "Grade School", "weighted-drop-policy", "Weighted drop policy",
        "Compute a weighted integer score after dropping exactly one assignment that minimizes its weighted contribution; ties drop the earliest assignment. Weights are positive and division rounds toward zero.",
        "struct WeightedMark { int score; int weight; };\nstruct DropResult { std::size_t dropped; int average; };",
        "std::optional<DropResult> weighted_drop_policy(const std::vector<WeightedMark>& marks)",
        "if(marks.size()<2)return std::nullopt;long long sum=0,weight=0;std::size_t drop=0;long long contribution=LLONG_MAX;for(std::size_t i=0;i<marks.size();++i){auto m=marks[i];if(m.score<0||m.score>100||m.weight<=0)return std::nullopt;long long c=static_cast<long long>(m.score)*m.weight;if(c<contribution){contribution=c;drop=i;}sum+=c;weight+=m.weight;}sum-=static_cast<long long>(marks[drop].score)*marks[drop].weight;weight-=marks[drop].weight;return DropResult{drop,static_cast<int>(sum/weight)};",
        "auto r=weighted_drop_policy({{50,1},{80,2},{90,1}});require_case(r&&r->dropped==0&&r->average==83);require_case(!weighted_drop_policy({{50,1}}));require_case(!weighted_drop_policy({{101,1},{0,1}}));",
        "checked weighted aggregation with stable minimum-contribution removal", ("grade", "weighted", "drop"),
    )
    add(
        "Grade School", "prerequisite-grade-closure", "Prerequisite grade closure",
        "Return courses whose transitive prerequisite closure all meet a minimum score. Courses, scores, and edges are explicit; unknown endpoints, duplicate courses, or cycles reject.",
        "struct CourseScore { std::string course; int score; };\nstruct Prerequisite { std::string course; std::string required; };",
        "std::optional<std::vector<std::string>> prerequisite_grade_closure(const std::vector<CourseScore>& scores, const std::vector<Prerequisite>& edges, int minimum_score)",
        "std::map<std::string,int> value;for(auto s:scores)if(s.course.empty()||s.score<0||s.score>100||!value.emplace(s.course,s.score).second)return std::nullopt;std::map<std::string,std::vector<std::string>> graph;std::set<std::pair<std::string,std::string>> unique;for(auto e:edges)if(!value.count(e.course)||!value.count(e.required)||!unique.emplace(e.course,e.required).second)return std::nullopt;else graph[e.course].push_back(e.required);std::map<std::string,int> state;std::function<std::optional<bool>(const std::string&)> ok=[&](const std::string&x)->std::optional<bool>{if(state[x]==1)return std::nullopt;if(state[x]==2)return value[x]>=minimum_score;state[x]=1;bool good=value[x]>=minimum_score;for(const auto&y:graph[x]){auto child=ok(y);if(!child)return std::nullopt;good=good&&*child;}state[x]=2;return good;};std::vector<std::string> out;for(const auto&item:value){auto good=ok(item.first);if(!good)return std::nullopt;if(*good)out.push_back(item.first);}return out;",
        "auto r=prerequisite_grade_closure({{\"a\",90},{\"b\",80},{\"c\",50}},{{\"a\",\"b\"},{\"b\",\"c\"}},60);require_case(r&&*r==std::vector<std::string>({}));require_case(prerequisite_grade_closure({{\"a\",90}}, {},60)->at(0)==\"a\");require_case(!prerequisite_grade_closure({{\"a\",90}},{{\"a\",\"x\"}},60));",
        "cycle-detecting prerequisite DFS with threshold closure", ("courses", "prerequisite", "closure"),
    )
    add(
        "Grade School", "section-median-deviation", "Section median deviation",
        "For each named section, return its lower median and the sum of absolute deviations from that median. Section names are unique and marks lie from zero through one hundred.",
        "struct SectionMarks { std::string section; std::vector<int> marks; };\nstruct MedianDeviation { std::string section; int median; long long deviation; };",
        "std::optional<std::vector<MedianDeviation>> section_median_deviation(const std::vector<SectionMarks>& sections)",
        "std::set<std::string> names;std::vector<MedianDeviation> out;for(auto s:sections){if(s.section.empty()||s.marks.empty()||!names.insert(s.section).second)return std::nullopt;for(int x:s.marks)if(x<0||x>100)return std::nullopt;std::sort(s.marks.begin(),s.marks.end());int median=s.marks[(s.marks.size()-1)/2];long long deviation=0;for(int x:s.marks)deviation+=std::llabs(static_cast<long long>(x)-median);out.push_back({s.section,median,deviation});}std::sort(out.begin(),out.end(),[](const auto&a,const auto&b){return a.section<b.section;});return out;",
        "auto r=section_median_deviation({{\"b\",{1,9,5}},{\"a\",{2,4}}});require_case(r&&r->front().section==\"a\"&&r->front().median==2&&r->back().deviation==8);require_case(section_median_deviation({})->empty());require_case(!section_median_deviation({{\"x\",{}}}));",
        "per-section lower-median selection and absolute-deviation reduction", ("section", "median", "deviation"),
    )

    add(
        "Kindergarten Garden", "seasonal-plot-rotation", "Seasonal plot rotation",
        "Apply seasonal cyclic shifts to a rectangular child-by-plot crop matrix and return each child's crop history. Shift values may be signed and child names are sorted unique.",
        "",
        "std::optional<std::map<std::string,std::vector<char>>> seasonal_plot_rotation(const std::vector<std::string>& children, const std::vector<std::vector<char>>& seasons, const std::vector<int>& shifts)",
        "if(children.empty())return seasons.empty()&&shifts.empty()?std::optional<std::map<std::string,std::vector<char>>>{{}}:std::nullopt;if(!std::is_sorted(children.begin(),children.end())||std::adjacent_find(children.begin(),children.end())!=children.end()||seasons.size()!=shifts.size())return std::nullopt;std::map<std::string,std::vector<char>> out;for(std::size_t s=0;s<seasons.size();++s){if(seasons[s].size()!=children.size())return std::nullopt;long long shift=shifts[s]%static_cast<long long>(children.size());if(shift<0)shift+=children.size();for(std::size_t i=0;i<children.size();++i)out[children[i]].push_back(seasons[s][(i+static_cast<std::size_t>(shift))%children.size()]);}return out;",
        "auto r=seasonal_plot_rotation({\"a\",\"b\",\"c\"},{{'A','B','C'},{'D','E','F'}},{1,-1});require_case(r&&r->at(\"a\")==std::vector<char>({'B','F'}));require_case(seasonal_plot_rotation({}, {},{})->empty());require_case(!seasonal_plot_rotation({\"b\",\"a\"},{},{}));",
        "signed modular season shifts into per-child histories", ("garden", "season", "rotation"),
    )
    add(
        "Kindergarten Garden", "watering-conflict-components", "Watering conflict components",
        "Build connected components of plots whose closed watering intervals overlap. Plot names are unique, intervals valid, and each component is returned as sorted names ordered by its first name.",
        "struct WateringSlot { std::string plot; int begin; int end; };",
        "std::optional<std::vector<std::vector<std::string>>> watering_conflict_components(const std::vector<WateringSlot>& slots)",
        "std::set<std::string> names;for(auto s:slots)if(s.plot.empty()||s.begin<0||s.begin>s.end||!names.insert(s.plot).second)return std::nullopt;std::vector<int> parent(slots.size());std::iota(parent.begin(),parent.end(),0);std::function<int(int)> find=[&](int x){return parent[x]==x?x:parent[x]=find(parent[x]);};for(std::size_t i=0;i<slots.size();++i)for(std::size_t j=i+1;j<slots.size();++j)if(std::max(slots[i].begin,slots[j].begin)<=std::min(slots[i].end,slots[j].end))parent[find(static_cast<int>(i))]=find(static_cast<int>(j));std::map<int,std::vector<std::string>> groups;for(std::size_t i=0;i<slots.size();++i)groups[find(static_cast<int>(i))].push_back(slots[i].plot);std::vector<std::vector<std::string>> out;for(auto&g:groups){std::sort(g.second.begin(),g.second.end());out.push_back(g.second);}std::sort(out.begin(),out.end());return out;",
        "auto r=watering_conflict_components({{\"a\",0,2},{\"b\",2,4},{\"c\",8,9}});require_case(r&&*r==std::vector<std::vector<std::string>>({{\"a\",\"b\"},{\"c\"}}));require_case(watering_conflict_components({})->empty());require_case(!watering_conflict_components({{\"x\",2,1}}));",
        "quadratic interval-overlap union-find with canonical components", ("watering", "conflict", "components"),
    )
    add(
        "Kindergarten Garden", "seed-packet-allocation", "Seed packet allocation",
        "Allocate indivisible seed packets to children in repeated priority order without exceeding each child's capacity. Return unallocated packet indices and assigned packet totals.",
        "struct ChildCapacity { std::string child; int capacity; };\nstruct PacketAllocation { std::map<std::string,int> totals; std::vector<std::size_t> unallocated; };",
        "std::optional<PacketAllocation> seed_packet_allocation(const std::vector<ChildCapacity>& children, const std::vector<int>& packets)",
        "std::set<std::string> names;PacketAllocation out;for(auto c:children)if(c.child.empty()||c.capacity<0||!names.insert(c.child).second)return std::nullopt;else out.totals[c.child]=0;for(std::size_t i=0;i<packets.size();++i){if(packets[i]<=0)return std::nullopt;bool placed=false;for(std::size_t step=0;step<children.size();++step){std::size_t index=(i+step)%children.size();auto c=children[index];if(out.totals[c.child]<=c.capacity-packets[i]){out.totals[c.child]+=packets[i];placed=true;break;}}if(!placed)out.unallocated.push_back(i);}return out;",
        "auto r=seed_packet_allocation({{\"a\",3},{\"b\",4}},{2,3,2,5});require_case(r&&r->totals.at(\"a\")==2&&r->totals.at(\"b\")==3&&r->unallocated==std::vector<std::size_t>({2,3}));require_case(seed_packet_allocation({},{})->totals.empty());require_case(!seed_packet_allocation({}, {0}));",
        "rotating-priority first-fit packet placement with rejection ledger", ("seed", "packets", "allocation"),
    )

    add(
        "Linked List", "multi-chain-weave", "Multi-chain weave",
        "Weave several integer chains by taking one item from each nonempty chain per round. Each input chain has an explicit maximum length and output size is overflow checked.",
        "",
        "std::optional<std::vector<int>> multi_chain_weave(const std::vector<std::vector<int>>& chains, std::size_t maximum_total)",
        "std::size_t total=0,longest=0;for(const auto&c:chains){if(total>maximum_total-c.size())return std::nullopt;total+=c.size();longest=std::max(longest,c.size());}std::vector<int> out;out.reserve(total);for(std::size_t position=0;position<longest;++position)for(const auto&c:chains)if(position<c.size())out.push_back(c[position]);return out;",
        "auto r=multi_chain_weave({{1,2,3},{4},{5,6}},6);require_case(r&&*r==std::vector<int>({1,4,5,2,6,3}));require_case(multi_chain_weave({},0)->empty());require_case(!multi_chain_weave({{1}},0));",
        "round-major stable weaving after total-size admission", ("chains", "weave", "stable"),
    )
    add(
        "Linked List", "pointer-reversal-checkpoints", "Pointer reversal checkpoints",
        "Reverse an indexed singly linked chain in groups of requested sizes and return the head index after every completed group. The chain must cover every node exactly once and group sizes are positive.",
        "struct LinkNode { int next; };",
        "std::optional<std::vector<int>> pointer_reversal_checkpoints(std::vector<LinkNode> nodes, int head, const std::vector<std::size_t>& groups)",
        "if(nodes.empty())return head==-1&&groups.empty()?std::optional<std::vector<int>>{{}}:std::nullopt;if(head<0||head>=static_cast<int>(nodes.size()))return std::nullopt;std::vector<int> order,seen(nodes.size());for(int x=head;x!=-1;x=nodes[x].next){if(x<0||x>=static_cast<int>(nodes.size())||seen[x]++)return std::nullopt;order.push_back(x);}if(order.size()!=nodes.size())return std::nullopt;std::vector<int> checkpoints;std::size_t cursor=0;for(auto length:groups){if(length==0||cursor+length>order.size())return std::nullopt;std::reverse(order.begin()+static_cast<std::ptrdiff_t>(cursor),order.begin()+static_cast<std::ptrdiff_t>(cursor+length));cursor+=length;checkpoints.push_back(order.front());}return checkpoints;",
        "auto r=pointer_reversal_checkpoints({{1},{2},{-1}},0,{2,1});require_case(r&&*r==std::vector<int>({1,1}));require_case(pointer_reversal_checkpoints({{-1}},0,{})->empty());require_case(!pointer_reversal_checkpoints({{0}},0,{}));",
        "whole-chain validation followed by bounded group-order reversals", ("pointer", "reversal", "checkpoints"),
    )
    add(
        "Linked List", "chain-segment-digests", "Chain segment digests",
        "Partition a fully reachable indexed value chain at declared one-based cut positions and compute a rolling digest for each segment modulo a caller modulus. Cuts are strictly increasing and may end at chain length.",
        "struct DigestNode { int value; int next; };",
        "std::optional<std::vector<std::uint64_t>> chain_segment_digests(const std::vector<DigestNode>& nodes, int head, const std::vector<std::size_t>& cuts, std::uint64_t modulus)",
        "if(modulus<257)return std::nullopt;std::vector<int> values,seen(nodes.size());for(int x=head;x!=-1;x=nodes[x].next){if(x<0||x>=static_cast<int>(nodes.size())||seen[x]++)return std::nullopt;values.push_back(nodes[x].value);}if(values.size()!=nodes.size())return std::nullopt;std::vector<std::size_t> boundaries=cuts;if(boundaries.empty()||boundaries.back()!=values.size())boundaries.push_back(values.size());std::size_t previous=0;std::vector<std::uint64_t> out;for(auto cut:boundaries){if(cut<=previous||cut>values.size())return std::nullopt;std::uint64_t d=0;for(std::size_t i=previous;i<cut;++i)d=(d*257+static_cast<std::uint64_t>(values[i]))%modulus;out.push_back(d);previous=cut;}return out;",
        "auto r=chain_segment_digests({{1,1},{2,2},{3,-1}},0,{2},1009);require_case(r&&r->size()==2&&r->at(0)==259&&r->at(1)==3);require_case(chain_segment_digests({},-1,{},257)->empty());require_case(!chain_segment_digests({{1,0}},0,{},257));",
        "cut-validated chain linearization and modular segment hashing", ("chain", "segments", "digest"),
    )

    add(
        "Parallel Letter Frequency", "parallel-trigram-boundaries", "Parallel trigram boundaries",
        "Count lowercase ASCII trigrams independently within each text using deterministic asynchronous shards. Nonletters reset the trigram window and worker count must be positive.",
        "",
        "std::optional<std::map<std::string,std::size_t>> parallel_trigram_boundaries(const std::vector<std::string>& texts, std::size_t workers)",
        "if(workers==0)return std::nullopt;workers=std::min(workers,std::max<std::size_t>(1,texts.size()));std::vector<std::future<std::map<std::string,std::size_t>>> jobs;for(std::size_t w=0;w<workers;++w)jobs.push_back(std::async(std::launch::async,[&,w]{std::map<std::string,std::size_t> local;for(std::size_t i=w;i<texts.size();i+=workers){std::string window;for(unsigned char c:texts[i]){if(c>='A'&&c<='Z')c=static_cast<unsigned char>(c-'A'+'a');if(c<'a'||c>'z'){window.clear();continue;}window.push_back(static_cast<char>(c));if(window.size()==3){++local[window];window.erase(window.begin());}}}return local;}));std::map<std::string,std::size_t> out;for(auto&j:jobs)for(auto item:j.get())out[item.first]+=item.second;return out;",
        "auto r=parallel_trigram_boundaries({\"Abcd!abc\",\"xbc\"},2);require_case(r&&r->at(\"abc\")==2&&r->at(\"bcd\")==1&&r->at(\"xbc\")==1);require_case(parallel_trigram_boundaries({},4)->empty());require_case(!parallel_trigram_boundaries({},0));",
        "strided asynchronous trigram maps with delimiter-reset windows", ("parallel", "trigram", "boundaries"),
    )
    add(
        "Parallel Letter Frequency", "parallel-vowel-run-extrema", "Parallel vowel run extrema",
        "Find the maximum ASCII-vowel run length in each text using bounded asynchronous workers. Runs never cross text boundaries and results retain input order.",
        "",
        "std::optional<std::vector<std::size_t>> parallel_vowel_run_extrema(const std::vector<std::string>& texts, std::size_t workers)",
        "if(workers==0)return std::nullopt;workers=std::min(workers,std::max<std::size_t>(1,texts.size()));std::vector<std::future<std::vector<std::pair<std::size_t,std::size_t>>>> jobs;for(std::size_t w=0;w<workers;++w)jobs.push_back(std::async(std::launch::async,[&,w]{std::vector<std::pair<std::size_t,std::size_t>> local;for(std::size_t i=w;i<texts.size();i+=workers){std::size_t best=0,run=0;for(unsigned char c:texts[i]){c=static_cast<unsigned char>(std::tolower(c));if(c=='a'||c=='e'||c=='i'||c=='o'||c=='u')best=std::max(best,++run);else run=0;}local.push_back({i,best});}return local;}));std::vector<std::size_t> out(texts.size());for(auto&j:jobs)for(auto item:j.get())out[item.first]=item.second;return out;",
        "auto r=parallel_vowel_run_extrema({\"queue!\",\"sky\",\"AEIOU\"},2);require_case(r&&*r==std::vector<std::size_t>({4,0,5}));require_case(parallel_vowel_run_extrema({},8)->empty());require_case(!parallel_vowel_run_extrema({},0));",
        "sharded local vowel-run scans with indexed result assembly", ("parallel", "vowel", "extrema"),
    )
    add(
        "Parallel Letter Frequency", "parallel-stable-letter-partition", "Parallel stable letter partition",
        "Partition each text into its ASCII letters and nonletters in stable order, processing texts asynchronously and returning one pair per input text. Worker count must be positive.",
        "struct TextPartition { std::string letters; std::string others; };",
        "std::optional<std::vector<TextPartition>> parallel_stable_letter_partition(const std::vector<std::string>& texts, std::size_t workers)",
        "if(workers==0)return std::nullopt;workers=std::min(workers,std::max<std::size_t>(1,texts.size()));std::vector<std::future<std::vector<std::pair<std::size_t,TextPartition>>>> jobs;for(std::size_t w=0;w<workers;++w)jobs.push_back(std::async(std::launch::async,[&,w]{std::vector<std::pair<std::size_t,TextPartition>> local;for(std::size_t i=w;i<texts.size();i+=workers){TextPartition p;for(unsigned char c:texts[i])((c>='A'&&c<='Z')||(c>='a'&&c<='z')?p.letters:p.others).push_back(static_cast<char>(c));local.push_back({i,std::move(p)});}return local;}));std::vector<TextPartition> out(texts.size());for(auto&j:jobs)for(auto&item:j.get())out[item.first]=std::move(item.second);return out;",
        "auto r=parallel_stable_letter_partition({\"a1-B\",\"!xy\"},2);require_case(r&&r->at(0).letters==\"aB\"&&r->at(0).others==\"1-\"&&r->at(1).letters==\"xy\");require_case(parallel_stable_letter_partition({},3)->empty());require_case(!parallel_stable_letter_partition({},0));",
        "asynchronous per-text stable dual-channel projection", ("parallel", "partition", "stable"),
    )

    add(
        "Phone Number", "dial-prefix-ambiguity-groups", "Dial prefix ambiguity groups",
        "Group canonical digit strings that are prefix-comparable. Input numbers are sorted unique nonempty digit strings; singleton components are retained.",
        "",
        "std::optional<std::vector<std::vector<std::string>>> dial_prefix_ambiguity_groups(const std::vector<std::string>& numbers)",
        "if(!std::is_sorted(numbers.begin(),numbers.end())||std::adjacent_find(numbers.begin(),numbers.end())!=numbers.end())return std::nullopt;for(const auto&n:numbers)if(n.empty()||!std::all_of(n.begin(),n.end(),[](char c){return c>='0'&&c<='9';}))return std::nullopt;std::vector<int> parent(numbers.size());std::iota(parent.begin(),parent.end(),0);std::function<int(int)> find=[&](int x){return parent[x]==x?x:parent[x]=find(parent[x]);};for(std::size_t i=0;i<numbers.size();++i)for(std::size_t j=i+1;j<numbers.size();++j)if(numbers[j].compare(0,numbers[i].size(),numbers[i])==0)parent[find(static_cast<int>(i))]=find(static_cast<int>(j));std::map<int,std::vector<std::string>> groups;for(std::size_t i=0;i<numbers.size();++i)groups[find(static_cast<int>(i))].push_back(numbers[i]);std::vector<std::vector<std::string>> out;for(auto&g:groups)out.push_back(g.second);std::sort(out.begin(),out.end());return out;",
        "auto r=dial_prefix_ambiguity_groups({\"1\",\"12\",\"3\",\"34\",\"345\"});require_case(r&&*r==std::vector<std::vector<std::string>>({{\"1\",\"12\"},{\"3\",\"34\",\"345\"}}));require_case(dial_prefix_ambiguity_groups({})->empty());require_case(!dial_prefix_ambiguity_groups({\"2\",\"1\"}));",
        "prefix-comparability union-find over canonical digit strings", ("phone", "prefix", "ambiguity"),
    )
    add(
        "Phone Number", "keypad-path-turn-count", "Keypad path turn count",
        "Map a digit string to coordinates on a standard telephone keypad and count direction changes between nonzero consecutive moves. Repeated digits do not create moves.",
        "",
        "std::optional<std::size_t> keypad_path_turn_count(const std::string& digits)",
        "const std::array<std::pair<int,int>,10> point={{{3,1},{0,0},{0,1},{0,2},{1,0},{1,1},{1,2},{2,0},{2,1},{2,2}}};std::optional<std::pair<int,int>> direction;std::size_t turns=0;for(std::size_t i=1;i<digits.size();++i){if(digits[i-1]<'0'||digits[i-1]>'9'||digits[i]<'0'||digits[i]>'9')return std::nullopt;auto a=point[digits[i-1]-'0'],b=point[digits[i]-'0'];std::pair<int,int> d{b.first-a.first,b.second-a.second};if(d==std::pair<int,int>{0,0})continue;if(direction&&*direction!=d)++turns;direction=d;}if(!digits.empty()&&!std::all_of(digits.begin(),digits.end(),[](char c){return c>='0'&&c<='9';}))return std::nullopt;return turns;",
        "require_case(keypad_path_turn_count(\"12369\")==2);require_case(keypad_path_turn_count(\"111\")==0);require_case(keypad_path_turn_count(\"\")==0);require_case(!keypad_path_turn_count(\"1x\"));",
        "coordinate move extraction with repeated-key suppression", ("keypad", "path", "turns"),
    )
    add(
        "Phone Number", "extension-range-compression", "Extension range compression",
        "Compress sorted unique nonnegative extension numbers into maximal consecutive inclusive ranges. Reject unsorted, duplicate, negative, or increment-overflow input.",
        "struct ExtensionRange { int first; int last; };",
        "std::optional<std::vector<ExtensionRange>> extension_range_compression(const std::vector<int>& extensions)",
        "if(!std::is_sorted(extensions.begin(),extensions.end())||std::adjacent_find(extensions.begin(),extensions.end())!=extensions.end()||(!extensions.empty()&&extensions.front()<0))return std::nullopt;std::vector<ExtensionRange> out;for(int x:extensions){if(out.empty()||out.back().last==INT_MAX||x!=out.back().last+1)out.push_back({x,x});else out.back().last=x;}return out;",
        "auto r=extension_range_compression({1,2,3,7,9,10});require_case(r&&r->size()==3&&r->front().first==1&&r->front().last==3&&r->back().last==10);require_case(extension_range_compression({})->empty());require_case(!extension_range_compression({2,1}));",
        "single-pass maximal consecutive-range coalescing", ("extension", "ranges", "compression"),
    )

    add(
        "Spiral Matrix", "spiral-diagonal-checkpoints", "Spiral diagonal checkpoints",
        "Traverse a rectangle clockwise from its top-left and return traversal indices at which the visited cell lies on either matrix diagonal. Dimensions and cell count are bounded.",
        "",
        "std::optional<std::vector<std::size_t>> spiral_diagonal_checkpoints(std::size_t rows, std::size_t columns, std::size_t maximum_cells)",
        "if(columns&&rows>maximum_cells/columns)return std::nullopt;std::size_t cells=rows*columns;if(cells>maximum_cells)return std::nullopt;std::vector<std::size_t> out;std::size_t top=0,left=0,bottom=rows,right=columns,index=0;auto visit=[&](std::size_t r,std::size_t c){if(r==c||r+c+1==columns)out.push_back(index);++index;};while(top<bottom&&left<right){for(std::size_t c=left;c<right;++c)visit(top,c);++top;for(std::size_t r=top;r<bottom;++r)visit(r,right-1);if(top<bottom&&left<--right){for(std::size_t c=right;c-->left;)visit(bottom-1,c);--bottom;}if(left<right){for(std::size_t r=bottom;r-->top;)visit(r,left);++left;}}return out;",
        "auto r=spiral_diagonal_checkpoints(2,3,6);require_case(r&&*r==std::vector<std::size_t>({0,2,4}));require_case(spiral_diagonal_checkpoints(0,5,0)->empty());require_case(!spiral_diagonal_checkpoints(3,3,8));",
        "boundary-shrinking spiral with indexed diagonal predicates", ("spiral", "diagonal", "checkpoints"),
    )
    add(
        "Spiral Matrix", "rectangular-ring-rotation", "Rectangular ring rotation",
        "Rotate each rectangular perimeter ring clockwise by its ring index plus one and return the transformed matrix. Input must be rectangular and total cells bounded.",
        "",
        "std::optional<std::vector<std::vector<int>>> rectangular_ring_rotation(std::vector<std::vector<int>> matrix, std::size_t maximum_cells)",
        "std::size_t rows=matrix.size(),columns=rows?matrix[0].size():0;for(const auto&r:matrix)if(r.size()!=columns)return std::nullopt;if(columns&&rows>maximum_cells/columns)return std::nullopt;for(std::size_t layer=0;layer<std::min(rows,columns+1)/2&&layer<rows-layer&&layer<columns-layer;++layer){std::vector<std::pair<std::size_t,std::size_t>> cells;std::size_t bottom=rows-1-layer,right=columns-1-layer;for(std::size_t c=layer;c<=right;++c)cells.push_back({layer,c});for(std::size_t r=layer+1;r<=bottom;++r)cells.push_back({r,right});if(bottom>layer)for(std::size_t c=right;c-->layer;)cells.push_back({bottom,c});if(right>layer)for(std::size_t r=bottom;r-->layer+1;)cells.push_back({r,layer});if(cells.size()>1){std::vector<int> values;for(auto p:cells)values.push_back(matrix[p.first][p.second]);std::rotate(values.rbegin(),values.rbegin()+static_cast<std::ptrdiff_t>((layer+1)%values.size()),values.rend());for(std::size_t i=0;i<cells.size();++i)matrix[cells[i].first][cells[i].second]=values[i];}}return matrix;",
        "auto r=rectangular_ring_rotation({{1,2,3},{4,5,6}},6);require_case(r&&*r==std::vector<std::vector<int>>({{4,1,2},{5,6,3}}));require_case(rectangular_ring_rotation({},0)->empty());require_case(!rectangular_ring_rotation({{1},{2,3}},4));",
        "ring coordinate extraction and layer-dependent cyclic rotation", ("matrix", "rings", "rotation"),
    )
    add(
        "Spiral Matrix", "obstacle-spiral-prefix", "Obstacle spiral prefix",
        "Follow a clockwise inward spiral through a rectangular grid and stop immediately before the first blocked cell. Return the unblocked coordinate prefix; blocked coordinates are unique and in range.",
        "struct MatrixCell { std::size_t row; std::size_t column; };",
        "std::optional<std::vector<MatrixCell>> obstacle_spiral_prefix(std::size_t rows, std::size_t columns, const std::vector<MatrixCell>& blocked)",
        "std::set<std::pair<std::size_t,std::size_t>> wall;for(auto p:blocked)if(p.row>=rows||p.column>=columns||!wall.emplace(p.row,p.column).second)return std::nullopt;std::vector<MatrixCell> out;bool stopped=false;auto visit=[&](std::size_t r,std::size_t c){if(stopped)return;if(wall.count({r,c}))stopped=true;else out.push_back({r,c});};std::size_t top=0,left=0,bottom=rows,right=columns;while(!stopped&&top<bottom&&left<right){for(std::size_t c=left;c<right;++c)visit(top,c);++top;for(std::size_t r=top;r<bottom;++r)visit(r,right-1);if(top<bottom&&left<--right){for(std::size_t c=right;c-->left;)visit(bottom-1,c);--bottom;}if(left<right){for(std::size_t r=bottom;r-->top;)visit(r,left);++left;}}return out;",
        "auto r=obstacle_spiral_prefix(2,3,{{1,2}});require_case(r&&r->size()==3&&r->back().row==0&&r->back().column==2);require_case(obstacle_spiral_prefix(0,4,{})->empty());require_case(!obstacle_spiral_prefix(1,1,{{1,0}}));",
        "short-circuiting spiral coordinate traversal against a wall set", ("spiral", "obstacle", "prefix"),
    )

    add(
        "Sublist", "minimal-cover-multiplicity", "Minimal cover multiplicity",
        "Find the shortest contiguous haystack window containing every pattern value with at least its pattern multiplicity. Ties prefer the earliest start; return no inner result when impossible.",
        "struct CoverWindow { std::size_t begin; std::size_t end; };",
        "std::optional<std::optional<CoverWindow>> minimal_cover_multiplicity(const std::vector<int>& haystack, const std::vector<int>& pattern)",
        "if(pattern.empty())return std::optional<CoverWindow>{CoverWindow{0,0}};std::map<int,int> need,have;for(int x:pattern)++need[x];std::size_t formed=0,left=0;std::optional<CoverWindow> best;for(std::size_t right=0;right<haystack.size();++right){int x=haystack[right];if(need.count(x)&&++have[x]==need[x])++formed;while(formed==need.size()){CoverWindow c{left,right+1};if(!best||c.end-c.begin<best->end-best->begin)best=c;int y=haystack[left++];if(need.count(y)&&have[y]--==need[y])--formed;}}return best;",
        "auto r=minimal_cover_multiplicity({1,2,1,3,2},{1,2,2});require_case(r&&*r&&(**r).begin==1&&(**r).end==5);auto e=minimal_cover_multiplicity({},{});require_case(e&&*e&&(**e).begin==0);auto n=minimal_cover_multiplicity({1},{2});require_case(n&&!*n);",
        "multiplicity-aware shrinking window with stable earliest optimum", ("sublist", "cover", "multiplicity"),
    )
    add(
        "Sublist", "alternating-subsequence-witness", "Alternating subsequence witness",
        "Return indices of a longest subsequence whose consecutive comparisons strictly alternate up and down. Equal values cannot extend the witness and earliest predecessor choices are retained.",
        "",
        "std::vector<std::size_t> alternating_subsequence_witness(const std::vector<int>& values)",
        "if(values.empty())return {};std::vector<std::size_t> out{0};int direction=0;for(std::size_t i=1;i<values.size();++i){int next=(values[i]>values[out.back()])-(values[i]<values[out.back()]);if(next==0)continue;if(direction==0||next!=direction){out.push_back(i);direction=next;}else out.back()=i;}return out;",
        "auto r=alternating_subsequence_witness({1,7,4,9,2,5});require_case(r==std::vector<std::size_t>({0,1,2,3,4,5}));require_case(alternating_subsequence_witness({1,2,3})==std::vector<std::size_t>({0,2}));require_case(alternating_subsequence_witness({}).empty());",
        "greedy extremum replacement with explicit comparison direction", ("subsequence", "alternating", "witness"),
    )
    add(
        "Sublist", "interval-pattern-occurrences", "Interval pattern occurrences",
        "Return starts where consecutive haystack differences equal a signed difference pattern. The empty pattern matches every single-element anchor including the position after the haystack.",
        "",
        "std::optional<std::vector<std::size_t>> interval_pattern_occurrences(const std::vector<long long>& haystack, const std::vector<long long>& differences)",
        "std::vector<std::size_t> out;if(differences.empty()){for(std::size_t i=0;i<=haystack.size();++i)out.push_back(i);return out;}if(haystack.size()<=differences.size())return out;for(std::size_t start=0;start+differences.size()<haystack.size();++start){bool match=true;for(std::size_t j=0;j<differences.size();++j){long long a=haystack[start+j],b=haystack[start+j+1];if((b>0&&a<LLONG_MIN+b)||(b<0&&a>LLONG_MAX+b)){match=false;break;}if(b-a!=differences[j]){match=false;break;}}if(match)out.push_back(start);}return out;",
        "auto r=interval_pattern_occurrences({1,3,6,8,11},{2,3});require_case(r&&*r==std::vector<std::size_t>({0,2}));require_case(interval_pattern_occurrences({},{})->size()==1);require_case(interval_pattern_occurrences({1},{1})->empty());",
        "checked adjacent-difference matching at every viable start", ("interval", "pattern", "occurrences"),
    )

    add(
        "Yacht", "held-dice-score-frontier", "Held dice score frontier",
        "For every possible face, score a held hand by face times occurrence count and return all faces attaining the maximum score. Dice and sides are validated and output faces ascend.",
        "struct ScoreFrontier { int score; std::vector<int> faces; };",
        "std::optional<ScoreFrontier> held_dice_score_frontier(const std::vector<int>& dice, int sides)",
        "if(sides<=0)return std::nullopt;std::vector<int> counts(static_cast<std::size_t>(sides+1));for(int d:dice)if(d<1||d>sides)return std::nullopt;else ++counts[d];ScoreFrontier out{0,{}};for(int face=1;face<=sides;++face){int score=face*counts[face];if(score>out.score)out={score,{face}};else if(score==out.score)out.faces.push_back(face);}return out;",
        "auto r=held_dice_score_frontier({2,2,5},6);require_case(r&&r->score==5&&r->faces==std::vector<int>({5}));require_case(held_dice_score_frontier({},3)->faces==std::vector<int>({1,2,3}));require_case(!held_dice_score_frontier({7},6));",
        "face histogram scoring with complete maximum tie frontier", ("dice", "score", "frontier"),
    )
    add(
        "Yacht", "single-reroll-target-probability", "Single reroll target probability",
        "For a held hand and target sum, count equally likely outcomes obtained by rerolling exactly one indexed die to every face. Return reduced numerator and denominator; empty hands have no experiment.",
        "struct Fraction { std::uint64_t numerator; std::uint64_t denominator; };",
        "std::optional<Fraction> single_reroll_target_probability(const std::vector<int>& dice, int sides, int target_sum)",
        "if(sides<=0||dice.empty())return std::nullopt;long long total=0;for(int d:dice)if(d<1||d>sides)return std::nullopt;else total+=d;std::uint64_t favorable=0,all=static_cast<std::uint64_t>(dice.size())*static_cast<std::uint64_t>(sides);for(int d:dice)for(int face=1;face<=sides;++face)favorable+=total-d+face==target_sum;std::uint64_t divisor=std::gcd(favorable,all);return Fraction{favorable/divisor,all/divisor};",
        "auto r=single_reroll_target_probability({1,2},6,7);require_case(r&&r->numerator==1&&r->denominator==6);auto z=single_reroll_target_probability({1},6,99);require_case(z&&z->numerator==0&&z->denominator==1);require_case(!single_reroll_target_probability({},6,0));",
        "indexed reroll outcome enumeration with rational reduction", ("reroll", "probability", "fraction"),
    )
    add(
        "Yacht", "category-conflict-graph", "Category conflict graph",
        "Build an undirected graph connecting scoring categories whose declared required-face sets overlap. Category names and face sets are canonical and graph adjacency is sorted.",
        "struct DiceCategory { std::string name; std::vector<int> required_faces; };",
        "std::optional<std::map<std::string,std::vector<std::string>>> category_conflict_graph(const std::vector<DiceCategory>& categories, int sides)",
        "if(sides<=0)return std::nullopt;std::map<std::string,std::vector<int>> faces;for(auto c:categories){if(c.name.empty()||!std::is_sorted(c.required_faces.begin(),c.required_faces.end())||std::adjacent_find(c.required_faces.begin(),c.required_faces.end())!=c.required_faces.end()||!faces.emplace(c.name,c.required_faces).second)return std::nullopt;for(int x:c.required_faces)if(x<1||x>sides)return std::nullopt;}std::map<std::string,std::vector<std::string>> out;for(const auto&a:faces)out[a.first];for(auto a=faces.begin();a!=faces.end();++a)for(auto b=std::next(a);b!=faces.end();++b){std::vector<int> common;std::set_intersection(a->second.begin(),a->second.end(),b->second.begin(),b->second.end(),std::back_inserter(common));if(!common.empty()){out[a->first].push_back(b->first);out[b->first].push_back(a->first);}}return out;",
        "auto r=category_conflict_graph({{\"a\",{1,2}},{\"b\",{2,3}},{\"c\",{6}}},6);require_case(r&&r->at(\"a\")==std::vector<std::string>({\"b\"})&&r->at(\"c\").empty());require_case(category_conflict_graph({},6)->empty());require_case(!category_conflict_graph({},0));",
        "pairwise sorted-set intersections into symmetric adjacency", ("category", "conflict", "graph"),
    )

    add(
        "Zebra Puzzle", "clue-implication-closure", "Clue implication closure",
        "Compute transitive implication closure over sorted unique proposition names and return all newly implied ordered pairs. Unknown, self, duplicate, or cyclic direct clues reject.",
        "struct Implication { std::string premise; std::string conclusion; };",
        "std::optional<std::vector<Implication>> clue_implication_closure(const std::vector<std::string>& propositions, const std::vector<Implication>& clues)",
        "if(!std::is_sorted(propositions.begin(),propositions.end())||std::adjacent_find(propositions.begin(),propositions.end())!=propositions.end())return std::nullopt;std::map<std::string,std::set<std::string>> reach;std::set<std::pair<std::string,std::string>> direct;for(auto c:clues)if(c.premise==c.conclusion||!std::binary_search(propositions.begin(),propositions.end(),c.premise)||!std::binary_search(propositions.begin(),propositions.end(),c.conclusion)||!direct.emplace(c.premise,c.conclusion).second)return std::nullopt;else reach[c.premise].insert(c.conclusion);for(const auto&k:propositions)for(const auto&i:propositions)if(reach[i].count(k))reach[i].insert(reach[k].begin(),reach[k].end());for(const auto&p:propositions)if(reach[p].count(p))return std::nullopt;std::vector<Implication> out;for(const auto&a:reach)for(const auto&b:a.second)if(!direct.count({a.first,b}))out.push_back({a.first,b});return out;",
        "auto r=clue_implication_closure({\"a\",\"b\",\"c\"},{{\"a\",\"b\"},{\"b\",\"c\"}});require_case(r&&r->size()==1&&r->front().premise==\"a\"&&r->front().conclusion==\"c\");require_case(clue_implication_closure({},{})->empty());require_case(!clue_implication_closure({\"a\",\"b\"},{{\"a\",\"b\"},{\"b\",\"a\"}}));",
        "ordered set-based transitive closure with cycle rejection", ("clue", "implication", "closure"),
    )
    add(
        "Zebra Puzzle", "domain-bipartite-support", "Domain bipartite support",
        "Return candidate edges that participate in at least one perfect matching between variables and values. Candidate rows are sorted unique and the bounded square domain has at most eight variables.",
        "struct SupportedEdge { std::size_t variable; int value; };",
        "std::optional<std::vector<SupportedEdge>> domain_bipartite_support(const std::vector<std::vector<int>>& candidates, int value_count)",
        "if(value_count<0||candidates.size()!=static_cast<std::size_t>(value_count)||candidates.size()>8)return std::nullopt;for(const auto&row:candidates)if(!std::is_sorted(row.begin(),row.end())||std::adjacent_find(row.begin(),row.end())!=row.end()||!std::all_of(row.begin(),row.end(),[&](int x){return x>=0&&x<value_count;}))return std::nullopt;std::set<std::pair<std::size_t,int>> supported;std::vector<int> assignment(candidates.size()),used(candidates.size());std::function<void(std::size_t)> rec=[&](std::size_t i){if(i==candidates.size()){for(std::size_t j=0;j<assignment.size();++j)supported.emplace(j,assignment[j]);return;}for(int x:candidates[i])if(!used[x]){used[x]=1;assignment[i]=x;rec(i+1);used[x]=0;}};rec(0);std::vector<SupportedEdge> out;for(auto e:supported)out.push_back({e.first,e.second});return out;",
        "auto r=domain_bipartite_support({{0,1},{0,1}},2);require_case(r&&r->size()==4);require_case(domain_bipartite_support({},0)->empty());require_case(domain_bipartite_support({{0},{}},2)->empty());require_case(!domain_bipartite_support({{1,0},{0}},2));",
        "bounded perfect-matching enumeration with unioned edge support", ("domain", "matching", "support"),
    )
    add(
        "Zebra Puzzle", "partial-order-layering", "Partial order layering",
        "Layer sorted unique labels under strict before-clues using deterministic Kahn traversal. Each layer contains all currently minimal labels; duplicate, unknown, self, or cyclic clues reject.",
        "struct BeforeClue { std::string earlier; std::string later; };",
        "std::optional<std::vector<std::vector<std::string>>> partial_order_layering(const std::vector<std::string>& labels, const std::vector<BeforeClue>& clues)",
        "if(!std::is_sorted(labels.begin(),labels.end())||std::adjacent_find(labels.begin(),labels.end())!=labels.end())return std::nullopt;std::map<std::string,std::set<std::string>> graph;std::map<std::string,int> indegree;for(const auto&x:labels)if(x.empty())return std::nullopt;else indegree[x]=0;for(auto c:clues)if(c.earlier==c.later||!indegree.count(c.earlier)||!indegree.count(c.later)||!graph[c.earlier].insert(c.later).second)return std::nullopt;else ++indegree[c.later];std::vector<std::vector<std::string>> out;std::size_t emitted=0;while(emitted<labels.size()){std::vector<std::string> layer;for(const auto&x:indegree)if(x.second==0)layer.push_back(x.first);if(layer.empty())return std::nullopt;out.push_back(layer);for(const auto&x:layer){indegree[x]=-1;++emitted;for(const auto&y:graph[x])--indegree[y];}}return out;",
        "auto r=partial_order_layering({\"a\",\"b\",\"c\",\"d\"},{{\"a\",\"c\"},{\"b\",\"c\"},{\"c\",\"d\"}});require_case(r&&*r==std::vector<std::vector<std::string>>({{\"a\",\"b\"},{\"c\"},{\"d\"}}));require_case(partial_order_layering({},{})->empty());require_case(!partial_order_layering({\"a\",\"b\"},{{\"a\",\"b\"},{\"b\",\"a\"}}));",
        "lexicographic all-minima Kahn layering with cycle detection", ("partial-order", "layers", "kahn"),
    )

    if len(specs) != 51:
        raise ValueError(f"expected 51 clean-room q86 specifications, got {len(specs)}")
    topics = tuple(dict.fromkeys(spec.topic for spec in specs))
    if len(topics) != 17 or any(sum(spec.topic == topic for spec in specs) != 3 for topic in topics):
        raise ValueError("q86 specifications must contain three tasks for each of 17 topics")
    return specs
