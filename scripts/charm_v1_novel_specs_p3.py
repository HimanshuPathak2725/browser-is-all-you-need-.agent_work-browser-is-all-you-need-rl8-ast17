#!/usr/bin/env python3
"""Independently authored CHARM V1 p3 task contracts.

The permanent batch code 18745 was reserved before these proposal bytes were
frozen.  No contract, API, target algorithm, or oracle is inherited from a
prior V1 planning lineage.
"""

from __future__ import annotations

import re


def build_specs(Spec):
    specs = []

    def add(topic, slug, title, contract, types, signature, body, tests, edges, strategy, tags):
        topic_ns = re.sub(r"[^a-z0-9]+", "_", topic.casefold()).strip("_")
        namespace = f"charm::v1p3_18745::{topic_ns}"
        definition_signature = signature
        for type_name in re.findall(r"(?:struct|class|enum\s+class)\s+([A-Za-z_][A-Za-z0-9_]*)", types):
            definition_signature = re.sub(
                rf"(?<!:)\b{re.escape(type_name)}\b", f"{namespace}::{type_name}",
                definition_signature,
            )
        match = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(", definition_signature)
        if match is None:
            raise ValueError(f"cannot qualify signature: {signature}")
        qualified = (definition_signature[:match.start(1)] + namespace + "::" +
                     definition_signature[match.start(1):])
        formatted = body.strip().replace(";", ";\n").replace("}", "}\n")
        definition = qualified + " {\n" + formatted + "\n}"
        test_source = f"using namespace {namespace};\nint main() {{\n{tests.strip()}\n    return 0;\n}}"
        specs.append(Spec(topic, slug, title, contract, types, signature, definition,
                          test_source, tuple(edges), strategy, tuple(tags)))

    add(
        "Allergies", "cooldown-safe-windows", "Cooldown-safe windows",
        "From timestamped allergen doses and per-allergen cooldown durations, return maximal half-open intervals within an observation horizon during which no cooldown is active. Doses are time-sorted, names are known, and arithmetic must remain in range.",
        "struct DoseEvent { int minute; std::string allergen; };\nstruct Cooldown { std::string allergen; int duration; };\nstruct SafeWindow { int begin; int end; };",
        "std::optional<std::vector<SafeWindow>> cooldown_safe_windows(int horizon, const std::vector<DoseEvent>& doses, const std::vector<Cooldown>& cooldowns)",
        """if(horizon<0)return std::nullopt;std::map<std::string,int> duration;for(const auto&c:cooldowns)if(c.allergen.empty()||c.duration<0||!duration.emplace(c.allergen,c.duration).second)return std::nullopt;int previous=-1;std::vector<std::pair<int,int>> blocked;for(const auto&d:doses){if(d.minute<0||d.minute>horizon||d.minute<previous||!duration.count(d.allergen))return std::nullopt;previous=d.minute;long long end=static_cast<long long>(d.minute)+duration[d.allergen];blocked.push_back({d.minute,static_cast<int>(std::min<long long>(horizon,end))});}std::sort(blocked.begin(),blocked.end());std::vector<SafeWindow> out;int cursor=0;for(auto interval:blocked){if(cursor<interval.first)out.push_back({cursor,interval.first});cursor=std::max(cursor,interval.second);}if(cursor<horizon)out.push_back({cursor,horizon});return out;""",
        """auto r=cooldown_safe_windows(10,{{2,"nut"},{5,"egg"}},{{"nut",4},{"egg",2}});assert(r&&r->size()==2&&r->at(0).begin==0&&r->at(1).begin==7&&r->at(1).end==10);
    assert(cooldown_safe_windows(0,{},{})->empty());
    assert(!cooldown_safe_windows(5,{{2,"x"}},{}));
    assert(!cooldown_safe_windows(5,{{3,"x"},{2,"x"}},{{"x",1}}));
    assert(!cooldown_safe_windows(-1,{},{}));""",
        ["horizon is nonnegative", "dose timestamps are nondecreasing", "every dose allergen has one cooldown", "overlapping cooldowns union", "safe windows are maximal and ordered"],
        "validated cooldown interval union followed by complement emission", ["cooldown", "interval-complement", "allergy"],
    )
    add(
        "Allergies", "panel-confusion-tallies", "Panel confusion tallies",
        "Compare a diagnostic panel with a truth set and return true-positive, false-positive, true-negative, and false-negative counts over a declared sorted allergen universe. Reject duplicate, unknown, or unsorted identities.",
        "struct ConfusionTallies { std::size_t true_positive; std::size_t false_positive; std::size_t true_negative; std::size_t false_negative; };",
        "std::optional<ConfusionTallies> panel_confusion_tallies(const std::vector<std::string>& universe, const std::vector<std::string>& truth, const std::vector<std::string>& positive)",
        """auto canonical=[](const std::vector<std::string>&v){return std::is_sorted(v.begin(),v.end())&&std::adjacent_find(v.begin(),v.end())==v.end()&&std::find(v.begin(),v.end(),\"\")==v.end();};if(!canonical(universe)||!canonical(truth)||!canonical(positive))return std::nullopt;for(const auto&x:truth)if(!std::binary_search(universe.begin(),universe.end(),x))return std::nullopt;for(const auto&x:positive)if(!std::binary_search(universe.begin(),universe.end(),x))return std::nullopt;ConfusionTallies out{};for(const auto&x:universe){bool t=std::binary_search(truth.begin(),truth.end(),x),p=std::binary_search(positive.begin(),positive.end(),x);if(t&&p)++out.true_positive;else if(!t&&p)++out.false_positive;else if(!t&&!p)++out.true_negative;else ++out.false_negative;}return out;""",
        """auto r=panel_confusion_tallies({"egg","milk","nut"},{"egg","nut"},{"egg","milk"});assert(r&&r->true_positive==1&&r->false_positive==1&&r->true_negative==0&&r->false_negative==1);
    auto e=panel_confusion_tallies({}, {}, {});assert(e&&e->true_negative==0);
    assert(!panel_confusion_tallies({"b","a"},{},{}));
    assert(!panel_confusion_tallies({"a"},{"x"},{}));""",
        ["all three lists are sorted unique", "universe names are nonempty", "truth and positives are subsets", "each universe member contributes exactly once", "empty universe returns zero tallies"],
        "three-way sorted membership classification", ["diagnostic", "confusion-matrix", "sets"],
    )
    add(
        "Allergies", "safe-substitution-distance", "Safe substitution distance",
        "Find the minimum directed substitution steps from an ingredient to any ingredient outside an allergen set. Edges and node names are explicit, duplicate edges reject, and lexical neighbor order breaks equal-distance ties in the returned path.",
        "struct Substitution { std::string from; std::string to; };",
        "std::optional<std::optional<std::vector<std::string>>> shortest_safe_substitution(const std::vector<std::string>& ingredients, const std::vector<Substitution>& substitutions, const std::vector<std::string>& allergens, const std::string& start)",
        """std::set<std::string> known(ingredients.begin(),ingredients.end());if(known.size()!=ingredients.size()||known.count(\"\")||!known.count(start))return std::nullopt;std::set<std::string> bad;for(const auto&x:allergens)if(!known.count(x)||!bad.insert(x).second)return std::nullopt;std::map<std::string,std::set<std::string>> graph;for(const auto&e:substitutions)if(!known.count(e.from)||!known.count(e.to)||!graph[e.from].insert(e.to).second)return std::nullopt;std::queue<std::vector<std::string>> q;std::set<std::string> seen{start};q.push({start});while(!q.empty()){auto path=q.front();q.pop();if(!bad.count(path.back()))return path;for(const auto&next:graph[path.back()])if(seen.insert(next).second){auto copy=path;copy.push_back(next);q.push(std::move(copy));}}return std::optional<std::vector<std::string>>{};""",
        """auto r=shortest_safe_substitution({"a","b","c"},{{"a","c"},{"a","b"}}, {"a","b"}, "a");assert(r&&*r&&**r==(std::vector<std::string>{"a","c"}));
    auto direct=shortest_safe_substitution({"a"},{},{},"a");assert(direct&&*direct&&(**direct).size()==1);
    auto none=shortest_safe_substitution({"a"},{},{"a"},"a");assert(none&&!*none);
    assert(!shortest_safe_substitution({"a"},{},{},"x"));""",
        ["ingredient domain is unique nonempty", "all allergens and edges are known", "duplicate directed edges reject", "start may already be safe", "breadth-first lexical traversal chooses the canonical path"],
        "lexically ordered breadth-first path search to the safe complement", ["substitution", "shortest-path", "allergy"],
    )

    add(
        "Bank Account", "basis-point-interest-ledger", "Basis-point interest ledger",
        "Apply a sequence of signed basis-point rates to an integer-cent balance, rounding each period's interest toward zero before the next period. Reject rates outside a fixed range or any multiplication/addition overflow.",
        "",
        "std::optional<long long> apply_basis_point_interest(long long opening_cents, const std::vector<int>& rates_basis_points)",
        """long long balance=opening_cents;for(int rate:rates_basis_points){if(rate<-10000||rate>10000)return std::nullopt;if(balance!=0&&std::llabs(balance)>LLONG_MAX/std::max(1,std::abs(rate)))return std::nullopt;long long interest=balance*rate/10000;if((interest>0&&balance>LLONG_MAX-interest)||(interest<0&&balance<LLONG_MIN-interest))return std::nullopt;balance+=interest;}return balance;""",
        """assert(apply_basis_point_interest(10000,{500,500})==11025);
    assert(apply_basis_point_interest(-101,{100})==-102);
    assert(apply_basis_point_interest(7,{})==7);
    assert(!apply_basis_point_interest(0,{10001}));
    assert(!apply_basis_point_interest(LLONG_MAX,{10000}));""",
        ["rates range from -10000 through 10000", "rounding occurs every period toward zero", "negative balances are supported", "multiplication is checked", "balance addition is checked"],
        "checked sequential fixed-point interest accrual", ["interest", "fixed-point", "ledger"],
    )
    add(
        "Bank Account", "bounded-cash-withdrawal", "Bounded cash withdrawal",
        "Choose counts of sorted unique banknote denominations with bounded availability to make an exact withdrawal. Minimize note count, then choose the lexicographically largest count vector so larger denominations are preferred. Distinguish invalid input from impossible amount.",
        "struct NoteStock { int denomination; int available; };",
        "std::optional<std::optional<std::vector<int>>> bounded_withdrawal(int amount, const std::vector<NoteStock>& stock)",
        """if(amount<0)return std::nullopt;for(std::size_t i=0;i<stock.size();++i)if(stock[i].denomination<=0||stock[i].available<0||(i&&stock[i-1].denomination<=stock[i].denomination))return std::nullopt;std::optional<std::vector<int>> best;int best_count=INT_MAX;std::vector<int> current(stock.size());std::function<void(std::size_t,int,int)> rec=[&](std::size_t i,int remaining,int count){if(i==stock.size()){if(remaining==0&&(count<best_count||(count==best_count&&(!best||current>*best)))){best=current;best_count=count;}return;}int maximum=std::min(stock[i].available,remaining/stock[i].denomination);for(int n=maximum;n>=0;--n){current[i]=n;rec(i+1,remaining-n*stock[i].denomination,count+n);}};rec(0,amount,0);return best;""",
        """auto r=bounded_withdrawal(12,{{10,1},{6,2},{1,9}});assert(r&&*r&&**r==(std::vector<int>{0,2,0}));
    auto zero=bounded_withdrawal(0,{});assert(zero&&*zero&&(**zero).empty());
    auto none=bounded_withdrawal(5,{{2,2}});assert(none&&!*none);
    assert(!bounded_withdrawal(-1,{}));
    assert(!bounded_withdrawal(1,{{1,1},{2,1}}));""",
        ["amount is nonnegative", "denominations are strictly descending positive", "availability is nonnegative", "minimum note count wins", "larger-denomination count vector breaks ties"],
        "bounded denomination search with exact objective and tie ordering", ["cash", "bounded-change", "optimization"],
    )
    add(
        "Bank Account", "statement-chain-validator", "Statement chain validator",
        "Validate an append-only statement whose each row carries the previous row's deterministic digest. The first previous digest is zero, sequence numbers start at one, and the final digest is returned. Reject malformed sequencing, empty descriptions, or amount/digest overflow.",
        "struct StatementRow { std::uint64_t sequence; long long cents; std::string description; std::uint64_t previous_digest; };",
        "std::optional<std::uint64_t> validate_statement_chain(const std::vector<StatementRow>& rows, std::uint64_t modulus)",
        """if(modulus<257)return std::nullopt;std::uint64_t digest=0;for(std::size_t i=0;i<rows.size();++i){const auto&r=rows[i];if(r.sequence!=i+1||r.description.empty()||r.previous_digest!=digest)return std::nullopt;auto add_mod=[&](std::uint64_t a,std::uint64_t b){return a>=modulus-b?a-(modulus-b):a+b;};auto mix=[&](std::uint64_t value){std::uint64_t product=0;for(int k=0;k<257;++k)product=add_mod(product,digest);digest=add_mod(product,value%modulus);};mix(r.sequence);mix(static_cast<std::uint64_t>(r.cents));for(unsigned char c:r.description)mix(c);}return digest;""",
        """auto first=validate_statement_chain({{1,5,"a",0}},1009);assert(first);assert(validate_statement_chain({{1,5,"a",0},{2,-1,"b",*first}},1009));
    assert(validate_statement_chain({},257)==0);
    assert(!validate_statement_chain({{2,0,"x",0}},1009));
    assert(!validate_statement_chain({{1,0,"",0}},1009));
    assert(!validate_statement_chain({},10));""",
        ["modulus is at least 257", "sequence is one-based contiguous", "first previous digest is zero", "descriptions are nonempty bytes", "every previous digest binds the full preceding prefix"],
        "streamed modular hash-chain verification", ["statement", "hash-chain", "integrity"],
    )

    add(
        "Binary Search Tree", "indexed-lca-batch", "Indexed LCA batch",
        "Answer lowest-common-ancestor queries in a rooted indexed binary tree. Every node is reachable exactly once, child and query indices are valid, and the returned ancestors follow query order. An empty tree accepts only an empty query list.",
        "struct ChildPair { int left; int right; };\nstruct NodeQuery { int first; int second; };",
        "std::optional<std::vector<int>> indexed_lca_batch(const std::vector<ChildPair>& children, int root, const std::vector<NodeQuery>& queries)",
        """if(children.empty())return root==-1&&queries.empty()?std::optional<std::vector<int>>{std::vector<int>{}}:std::nullopt;if(root<0||root>=static_cast<int>(children.size()))return std::nullopt;std::vector<int> parent(children.size(),-2),depth(children.size());parent[root]=-1;std::queue<int> q;q.push(root);while(!q.empty()){int node=q.front();q.pop();for(int child:{children[node].left,children[node].right})if(child!=-1){if(child<0||child>=static_cast<int>(children.size())||parent[child]!=-2)return std::nullopt;parent[child]=node;depth[child]=depth[node]+1;q.push(child);}}if(std::find(parent.begin(),parent.end(),-2)!=parent.end())return std::nullopt;std::vector<int> out;for(auto query:queries){int a=query.first,b=query.second;if(a<0||b<0||a>=static_cast<int>(children.size())||b>=static_cast<int>(children.size()))return std::nullopt;while(depth[a]>depth[b])a=parent[a];while(depth[b]>depth[a])b=parent[b];while(a!=b){a=parent[a];b=parent[b];}out.push_back(a);}return out;""",
        """auto r=indexed_lca_batch({{1,2},{3,-1},{-1,-1},{-1,-1}},0,{{3,2},{1,3}});assert(r&&*r==(std::vector<int>{0,1}));
    assert(indexed_lca_batch({},-1,{})->empty());
    assert(!indexed_lca_batch({},0,{}));
    assert(!indexed_lca_batch({{1,1},{-1,-1}},0,{}));
    assert(!indexed_lca_batch({{-1,-1}},0,{{0,1}}));""",
        ["tree identities are indexed", "every node is reachable exactly once", "queries are range checked", "a node may be its own ancestor", "answers preserve query order"],
        "breadth-first parent/depth construction followed by synchronized ascent", ["lca", "indexed-tree", "batch-query"],
    )
    add(
        "Binary Search Tree", "vertical-column-sums", "Vertical column sums",
        "Compute sums by horizontal column in an indexed binary tree, assigning left children column minus one and right children plus one. Return ascending column keys and reject cycles, shared nodes, invalid indices, or sum overflow.",
        "struct ValueChildren { long long value; int left; int right; };",
        "std::optional<std::map<int,long long>> vertical_column_sums(const std::vector<ValueChildren>& nodes, int root)",
        """if(nodes.empty())return root==-1?std::optional<std::map<int,long long>>{std::map<int,long long>{}}:std::nullopt;if(root<0||root>=static_cast<int>(nodes.size()))return std::nullopt;std::set<int> seen;std::queue<std::pair<int,int>> q;q.push({root,0});std::map<int,long long> sums;while(!q.empty()){auto[node,column]=q.front();q.pop();if(!seen.insert(node).second)return std::nullopt;long long&sum=sums[column];if((nodes[node].value>0&&sum>LLONG_MAX-nodes[node].value)||(nodes[node].value<0&&sum<LLONG_MIN-nodes[node].value))return std::nullopt;sum+=nodes[node].value;for(auto child:std::array<std::pair<int,int>,2>{{{nodes[node].left,column-1},{nodes[node].right,column+1}}})if(child.first!=-1){if(child.first<0||child.first>=static_cast<int>(nodes.size()))return std::nullopt;q.push(child);}}if(seen.size()!=nodes.size())return std::nullopt;return sums;""",
        """auto r=vertical_column_sums({{1,1,2},{2,-1,-1},{3,-1,-1}},0);assert(r&&r->at(-1)==2&&r->at(0)==1&&r->at(1)==3);
    assert(vertical_column_sums({},-1)->empty());
    assert(!vertical_column_sums({{1,0,-1}},0));
    assert(!vertical_column_sums({{1,-1,-1},{2,-1,-1}},0));""",
        ["empty tree uses root -1", "all nodes are reached once", "columns are signed", "output map is ascending", "column sums are overflow checked"],
        "breadth-first coordinate propagation and checked ordered aggregation", ["vertical-order", "tree", "aggregation"],
    )
    add(
        "Binary Search Tree", "mirror-pair-mismatch-count", "Mirror pair mismatch count",
        "Count positions whose keys differ when a tree is compared with its mirror. Missing-versus-present positions count once, while matching absent pairs stop. Reject invalid, cyclic, shared, or unreachable indexed trees.",
        "struct MirrorNode { int key; int left; int right; };",
        "std::optional<std::size_t> mirror_pair_mismatches(const std::vector<MirrorNode>& nodes, int root)",
        """if(nodes.empty())return root==-1?std::optional<std::size_t>{0}:std::nullopt;if(root<0||root>=static_cast<int>(nodes.size()))return std::nullopt;std::set<int> reachable;std::function<bool(int)> visit=[&](int x){if(x==-1)return true;if(x<0||x>=static_cast<int>(nodes.size())||!reachable.insert(x).second)return false;return visit(nodes[x].left)&&visit(nodes[x].right);};if(!visit(root)||reachable.size()!=nodes.size())return std::nullopt;std::size_t count=0;std::queue<std::pair<int,int>> q;q.push({root,root});while(!q.empty()){auto[a,b]=q.front();q.pop();if(a==-1&&b==-1)continue;if(a==-1||b==-1){++count;continue;}if(nodes[a].key!=nodes[b].key)++count;q.push({nodes[a].left,nodes[b].right});q.push({nodes[a].right,nodes[b].left});}return count/2;""",
        """assert(mirror_pair_mismatches({{1,1,2},{2,-1,-1},{2,-1,-1}},0)==0);
    assert(mirror_pair_mismatches({{1,1,2},{2,-1,-1},{3,-1,-1}},0)==1);
    assert(mirror_pair_mismatches({},-1)==0);
    assert(!mirror_pair_mismatches({{1,0,-1}},0));
    assert(!mirror_pair_mismatches({{1,-1,-1},{2,-1,-1}},0));""",
        ["tree is fully reachable without sharing", "root is paired with itself", "missing/present asymmetry counts", "symmetric unequal keys count as one pair", "absent/absent branches terminate"],
        "mirrored pair traversal over a separately validated indexed tree", ["mirror", "mismatch", "tree"],
    )

    add(
        "Circular Buffer", "cyclic-window-median", "Cyclic window median",
        "Return the lower median of each fixed-length cyclic window beginning at every ring position. Window length lies from one through ring size; even windows use the smaller middle value. Empty rings accept only window zero and return empty.",
        "",
        "std::optional<std::vector<int>> cyclic_window_medians(const std::vector<int>& ring, std::size_t window)",
        """if(ring.empty())return window==0?std::optional<std::vector<int>>{std::vector<int>{}}:std::nullopt;if(window==0||window>ring.size())return std::nullopt;std::vector<int> out;for(std::size_t start=0;start<ring.size();++start){std::vector<int> values;for(std::size_t i=0;i<window;++i)values.push_back(ring[(start+i)%ring.size()]);std::nth_element(values.begin(),values.begin()+(window-1)/2,values.end());out.push_back(values[(window-1)/2]);}return out;""",
        """assert(cyclic_window_medians({4,1,3},2).value()==(std::vector<int>{1,1,3}));
    assert(cyclic_window_medians({2},1).value()==(std::vector<int>{2}));
    assert(cyclic_window_medians({},0)->empty());
    assert(!cyclic_window_medians({},1));
    assert(!cyclic_window_medians({1},0));""",
        ["each ring position starts one window", "windows wrap", "lower median defines even windows", "nonempty window is bounded", "empty ring requires zero window"],
        "per-origin bounded selection on cyclic slices", ["median", "cyclic-window", "selection"],
    )
    add(
        "Circular Buffer", "josephus-elimination-rounds", "Josephus elimination rounds",
        "Simulate circular elimination of uniquely named participants using a positive step that counts the current participant as one. Return elimination order including the survivor; reject empty names, duplicate names, or zero step.",
        "",
        "std::optional<std::vector<std::string>> josephus_order(const std::vector<std::string>& participants, std::size_t step)",
        """if(step==0)return std::nullopt;std::set<std::string> unique(participants.begin(),participants.end());if(unique.size()!=participants.size()||unique.count(\"\"))return std::nullopt;std::vector<std::string> active=participants,out;std::size_t index=0;while(!active.empty()){index=(index+(step-1)%active.size())%active.size();out.push_back(active[index]);active.erase(active.begin()+static_cast<std::ptrdiff_t>(index));if(!active.empty())index%=active.size();}return out;""",
        """assert(josephus_order({"a","b","c","d"},2).value()==(std::vector<std::string>{"b","d","c","a"}));
    assert(josephus_order({},3)->empty());
    assert(!josephus_order({"a"},0));
    assert(!josephus_order({"a","a"},1));
    assert(!josephus_order({""},1));""",
        ["step is positive", "participant names are unique nonempty", "current position counts as one", "counting resumes after removed position", "survivor is final output"],
        "indexed vector erasure with modular counting", ["josephus", "elimination", "circular"],
    )
    add(
        "Circular Buffer", "modular-ring-convolution", "Modular ring convolution",
        "Compute circular convolution of equally sized integer rings modulo a positive modulus, normalizing negative inputs. Reject unequal sizes, invalid modulus, or intermediate size overflow; empty equal rings return empty.",
        "",
        "std::optional<std::vector<long long>> modular_ring_convolution(const std::vector<long long>& left, const std::vector<long long>& right, long long modulus)",
        """if(left.size()!=right.size()||modulus<=0)return std::nullopt;using U=unsigned long long;const U m=static_cast<U>(modulus);auto add_mod=[&](U a,U b){return a>=m-b?a-(m-b):a+b;};auto multiply=[&](U a,U b){U result=0;while(b){if(b&1U)result=add_mod(result,a);b>>=1U;if(b)a=add_mod(a,a);}return result;};std::vector<long long> out(left.size());for(std::size_t k=0;k<left.size();++k){U sum=0;for(std::size_t i=0;i<left.size();++i){long long av=left[i]%modulus;if(av<0)av+=modulus;long long bv=right[(k+left.size()-i)%left.size()]%modulus;if(bv<0)bv+=modulus;sum=add_mod(sum,multiply(static_cast<U>(av),static_cast<U>(bv)));}out[k]=static_cast<long long>(sum);}return out;""",
        """assert(modular_ring_convolution({1,2,3},{4,5,6},100).value()==(std::vector<long long>{31,31,28}));
    assert(modular_ring_convolution({}, {}, 7)->empty());
    assert(modular_ring_convolution({-1},{2},5).value()==(std::vector<long long>{3}));
    assert(!modular_ring_convolution({1},{1,2},5));
    assert(!modular_ring_convolution({}, {}, 0));""",
        ["ring lengths match", "modulus is positive", "negative values normalize", "indexing is circular", "wide products reduce before narrowing"],
        "wide modular circular convolution", ["convolution", "modular", "ring"],
    )

    add(
        "Clock", "clock-hand-angle-fraction", "Clock hand angle fraction",
        "Return the smaller angle between hour and minute hands as a reduced fraction of one degree for a normalized 12-hour time with integer seconds. Reject invalid components and represent exact coincidences as zero over one.",
        "struct DegreeFraction { long long numerator; long long denominator; };",
        "std::optional<DegreeFraction> clock_hand_angle(int hour, int minute, int second)",
        """if(hour<0||hour>=12||minute<0||minute>=60||second<0||second>=60)return std::nullopt;long long hour_ticks=hour*3600+minute*60+second;long long minute_ticks=(minute*60+second)*12;long long diff=std::llabs(hour_ticks-minute_ticks)%43200;diff=std::min(diff,43200-diff);long long numerator=diff,denominator=120;long long g=std::gcd(numerator,denominator);if(g==0)g=denominator;return DegreeFraction{numerator/g,denominator/g};""",
        """auto r=clock_hand_angle(3,0,0);assert(r&&r->numerator==90&&r->denominator==1);
    auto c=clock_hand_angle(0,0,0);assert(c&&c->numerator==0&&c->denominator==1);
    auto h=clock_hand_angle(6,0,0);assert(h&&h->numerator==180);
    assert(!clock_hand_angle(12,0,0));
    assert(!clock_hand_angle(0,60,0));""",
        ["time is normalized 12-hour", "seconds affect both hands", "smaller angle ranges through 180", "fraction is reduced", "zero denominator normalizes to one"],
        "integer clock ticks converted to an exact reduced angular fraction", ["analog-clock", "rational", "angle"],
    )
    add(
        "Clock", "rollover-lap-durations", "Rollover lap durations",
        "Convert readings from a modular timer into forward lap durations. Each later reading advances by its nonnegative modular distance, while an equal reading means zero rather than a full wrap. Reject invalid modulus or readings.",
        "",
        "std::optional<std::vector<int>> rollover_lap_durations(int modulus, const std::vector<int>& readings)",
        """if(modulus<=0)return std::nullopt;for(int x:readings)if(x<0||x>=modulus)return std::nullopt;std::vector<int> out;for(std::size_t i=1;i<readings.size();++i)out.push_back((readings[i]-readings[i-1]+modulus)%modulus);return out;""",
        """assert(rollover_lap_durations(10,{8,1,1,6}).value()==(std::vector<int>{3,0,5}));
    assert(rollover_lap_durations(5,{})->empty());
    assert(rollover_lap_durations(5,{2})->empty());
    assert(!rollover_lap_durations(0,{}));
    assert(!rollover_lap_durations(5,{5}));""",
        ["modulus is positive", "readings lie in canonical range", "first reading establishes origin only", "equal readings yield zero", "wrap uses least forward distance"],
        "adjacent modular difference projection", ["timer", "rollover", "laps"],
    )
    add(
        "Clock", "seven-segment-clock-cost", "Seven-segment clock cost",
        "Count how many seven-segment display segments illuminate across an inclusive sequence of HH:MM minute readings on a 24-hour cyclic clock. Both endpoints are normalized minute-of-day and at most one full cycle is traversed.",
        "",
        "std::optional<long long> seven_segment_clock_cost(int begin_minute, int end_minute)",
        """if(begin_minute<0||begin_minute>=1440||end_minute<0||end_minute>=1440)return std::nullopt;const std::array<int,10> segments={6,2,5,5,4,5,6,3,7,6};long long total=0;int current=begin_minute;for(int count=0;count<1440;++count){int h=current/60,m=current%60;total+=segments[h/10]+segments[h%10]+segments[m/10]+segments[m%10];if(current==end_minute)return total;current=(current+1)%1440;}return std::nullopt;""",
        """assert(seven_segment_clock_cost(0,0)==24);
    assert(seven_segment_clock_cost(0,1)==44);
    assert(seven_segment_clock_cost(1439,0)==45);""",
        ["endpoints are normalized", "both endpoints are included", "midnight wrap is permitted", "at most 1440 displays are counted", "leading zeroes illuminate"],
        "bounded cyclic display enumeration with digit lookup", ["seven-segment", "clock", "enumeration"],
    )

    add(
        "Complex Numbers", "complex-linear-fit", "Complex linear fit",
        "Fit a complex scalar coefficient minimizing squared error from predictor samples to response samples, using the closed-form conjugate dot product. Reject length mismatch, non-finite values, or a zero predictor norm.",
        "",
        "std::optional<std::complex<double>> complex_linear_fit(const std::vector<std::complex<double>>& predictors, const std::vector<std::complex<double>>& responses)",
        """if(predictors.size()!=responses.size())return std::nullopt;auto finite=[](auto z){return std::isfinite(z.real())&&std::isfinite(z.imag());};std::complex<double> numerator{};double denominator=0;for(std::size_t i=0;i<predictors.size();++i){if(!finite(predictors[i])||!finite(responses[i]))return std::nullopt;numerator+=std::conj(predictors[i])*responses[i];denominator+=std::norm(predictors[i]);}if(denominator==0||!std::isfinite(denominator)||!finite(numerator))return std::nullopt;auto result=numerator/denominator;return finite(result)?std::optional<std::complex<double>>{result}:std::nullopt;""",
        """auto r=complex_linear_fit({{1,0},{0,1}},{{2,0},{0,2}});assert(r&&std::abs(*r-std::complex<double>{2,0})<1e-12);
    assert(!complex_linear_fit({},{}));
    assert(!complex_linear_fit({{0,0}},{{1,0}}));
    assert(!complex_linear_fit({{1,0}},{}));""",
        ["vector lengths match", "all components are finite", "zero predictor norm rejects", "coefficient uses conjugate predictor dot product", "result must remain finite"],
        "closed-form one-parameter complex least squares", ["least-squares", "complex", "fit"],
    )
    add(
        "Complex Numbers", "stable-quadratic-roots", "Stable quadratic roots",
        "Solve a real-coefficient quadratic into two complex roots using a cancellation-resistant branch, returning roots in lexicographic real/imaginary order. Reject non-finite coefficients or zero leading coefficient.",
        "",
        "std::optional<std::array<std::complex<double>,2>> stable_quadratic_roots(double a, double b, double c)",
        """if(!std::isfinite(a)||!std::isfinite(b)||!std::isfinite(c)||a==0)return std::nullopt;std::complex<double> discriminant=std::complex<double>(b*b-4*a*c,0);auto root=std::sqrt(discriminant);std::complex<double> q=-0.5*(b+(b>=0?root:-root));std::complex<double> first,second;if(q==std::complex<double>{})first=second=-b/(2*a);else{first=q/a;second=c/q;}auto less=[](auto x,auto y){return std::make_pair(x.real(),x.imag())<std::make_pair(y.real(),y.imag());};if(less(second,first))std::swap(first,second);return std::array<std::complex<double>,2>{first,second};""",
        """auto r=stable_quadratic_roots(1,-3,2);assert(r&&std::abs(r->at(0).real()-1)<1e-12&&std::abs(r->at(1).real()-2)<1e-12);
    auto c=stable_quadratic_roots(1,0,1);assert(c&&c->at(0).imag()<0&&c->at(1).imag()>0);
    assert(!stable_quadratic_roots(0,1,1));
    assert(!stable_quadratic_roots(std::numeric_limits<double>::infinity(),1,1));""",
        ["leading coefficient is nonzero", "coefficients are finite", "real and conjugate roots are supported", "stable q branch reduces cancellation", "roots sort by real then imaginary"],
        "cancellation-resistant quadratic formula with complex discriminant", ["quadratic", "complex-roots", "numerical"],
    )
    add(
        "Complex Numbers", "polygon-winding-number", "Polygon winding number",
        "Compute the signed winding number of a closed complex polygon around a query point using oriented ray crossings. Reject non-finite coordinates, fewer than three vertices, or a query lying exactly on an edge.",
        "",
        "std::optional<int> polygon_winding_number(const std::vector<std::complex<double>>& vertices, std::complex<double> point)",
        """auto finite=[](auto z){return std::isfinite(z.real())&&std::isfinite(z.imag());};if(vertices.size()<3||!finite(point)||!std::all_of(vertices.begin(),vertices.end(),finite))return std::nullopt;int winding=0;for(std::size_t i=0;i<vertices.size();++i){auto a=vertices[i]-point,b=vertices[(i+1)%vertices.size()]-point;double cross=a.real()*b.imag()-a.imag()*b.real();double dot=a.real()*b.real()+a.imag()*b.imag();if(std::abs(cross)<1e-12&&dot<=0)return std::nullopt;if(a.imag()<=0&&b.imag()>0&&cross>0)++winding;if(a.imag()>0&&b.imag()<=0&&cross<0)--winding;}return winding;""",
        """assert(polygon_winding_number({{0,0},{2,0},{2,2},{0,2}},{1,1})==1);
    assert(polygon_winding_number({{0,0},{0,2},{2,2},{2,0}},{1,1})==-1);
    assert(polygon_winding_number({{0,0},{2,0},{2,2}},{9,9})==0);
    assert(!polygon_winding_number({{0,0},{1,0}},{0,0}));
    assert(!polygon_winding_number({{0,0},{2,0},{2,2}},{1,0}));""",
        ["polygon has at least three finite vertices", "query is finite", "on-edge query rejects", "orientation determines sign", "outside polygons return zero"],
        "oriented half-open ray-crossing accumulation", ["winding-number", "complex-plane", "geometry"],
    )

    add(
        "Crypto Square", "autokey-vigenere", "Autokey Vigenere",
        "Encode or decode lowercase ASCII letters with a lowercase primer and plaintext-autokey Vigenere stream. Nonletters are preserved without consuming key material. Reject empty or malformed primer and malformed alphabetic input case.",
        "enum class CipherDirection { encode, decode };",
        "std::optional<std::string> autokey_vigenere(std::string_view text, std::string_view primer, CipherDirection direction)",
        """if(primer.empty()||!std::all_of(primer.begin(),primer.end(),[](char c){return c>='a'&&c<='z';}))return std::nullopt;std::string out;std::vector<int> key;for(char c:primer)key.push_back(c-'a');std::size_t used=0;for(char c:text){if(c>='A'&&c<='Z')return std::nullopt;if(c<'a'||c>'z'){out.push_back(c);continue;}int input=c-'a',shift=key[used],plain=direction==CipherDirection::encode?input:(input-shift+26)%26,coded=direction==CipherDirection::encode?(input+shift)%26:plain;out.push_back(static_cast<char>('a'+coded));key.push_back(plain);++used;}return out;""",
        """auto e=autokey_vigenere("attack at dawn","queen",CipherDirection::encode);assert(e&&autokey_vigenere(*e,"queen",CipherDirection::decode)==std::optional<std::string>{"attack at dawn"});
    assert(autokey_vigenere("", "a", CipherDirection::encode)==std::optional<std::string>{""});
    assert(!autokey_vigenere("abc","",CipherDirection::encode));
    assert(!autokey_vigenere("Abc","a",CipherDirection::encode));""",
        ["primer is nonempty lowercase", "alphabetic text must be lowercase", "nonletters are preserved", "nonletters do not consume key", "decoded plaintext extends the key"],
        "stateful plaintext-autokey substitution with reversible streaming", ["vigenere", "autokey", "codec"],
    )
    add(
        "Crypto Square", "affine-key-recovery", "Affine key recovery",
        "Recover all affine-cipher keys modulo a declared alphabet size consistent with known plaintext/ciphertext symbol pairs. Keys require a multiplier coprime to the modulus; return pairs sorted by multiplier then offset.",
        "struct SymbolPair { int plain; int cipher; };\nstruct AffineKey { int multiplier; int offset; };",
        "std::optional<std::vector<AffineKey>> recover_affine_keys(int modulus, const std::vector<SymbolPair>& known_pairs)",
        """if(modulus<=1)return std::nullopt;for(auto p:known_pairs)if(p.plain<0||p.plain>=modulus||p.cipher<0||p.cipher>=modulus)return std::nullopt;std::vector<AffineKey> out;for(int a=0;a<modulus;++a)if(std::gcd(a,modulus)==1)for(int b=0;b<modulus;++b){bool ok=true;for(auto p:known_pairs)ok=ok&&(static_cast<long long>(a)*p.plain+b)%modulus==p.cipher;if(ok)out.push_back({a,b});}return out;""",
        """auto r=recover_affine_keys(26,{{0,3},{1,8}});assert(r&&r->size()==1&&r->at(0).multiplier==5&&r->at(0).offset==3);
    assert(recover_affine_keys(3,{})->size()==6);
    assert(!recover_affine_keys(1,{}));
    assert(!recover_affine_keys(5,{{5,0}}));""",
        ["modulus exceeds one", "symbols lie in canonical modular range", "multiplier is invertible", "all known pairs constrain each key", "output ordering is canonical"],
        "bounded exhaustive invertible affine parameter search", ["affine-cipher", "key-recovery", "modular"],
    )
    add(
        "Crypto Square", "bit-plane-interleave", "Bit plane interleave",
        "Interleave equal-length byte channels bit-plane first: for each bit from most to least significant, append that bit for every channel byte at each position, packed most-significant-bit first. Return packed bytes plus exact bit count.",
        "struct PackedBits { std::vector<unsigned char> bytes; std::size_t bit_count; };",
        "std::optional<PackedBits> interleave_bit_planes(const std::vector<std::vector<unsigned char>>& channels)",
        """std::size_t width=channels.empty()?0:channels[0].size();for(const auto&c:channels)if(c.size()!=width)return std::nullopt;PackedBits out{{},channels.size()*width*8};out.bytes.assign((out.bit_count+7)/8,0);std::size_t cursor=0;for(int bit=7;bit>=0;--bit)for(std::size_t position=0;position<width;++position)for(const auto&channel:channels){if((channel[position]>>bit)&1U)out.bytes[cursor/8]|=static_cast<unsigned char>(1U<<(7-cursor%8));++cursor;}return out;""",
        """auto r=interleave_bit_planes({{0x80},{0x40}});assert(r&&r->bit_count==16&&r->bytes.size()==2&&r->bytes[0]==0x90);
    auto e=interleave_bit_planes({});assert(e&&e->bit_count==0&&e->bytes.empty());
    assert(interleave_bit_planes({{}, {}})->bytes.empty());
    assert(!interleave_bit_planes({{1},{1,2}}));""",
        ["channel widths match", "bit planes descend from seven to zero", "position precedes channel within each plane", "packed output uses MSB first", "exact bit count is returned"],
        "deterministic three-axis bit-plane packing", ["bit-plane", "interleave", "packing"],
    )

    add(
        "Diamond", "diamond-perimeter-coordinates", "Diamond perimeter coordinates",
        "Enumerate integer coordinates at exactly a Manhattan radius from a center, starting at the top vertex and proceeding clockwise without repeating the start. Radius zero returns only the center; reject negative radius or coordinate overflow.",
        "struct Point { long long row; long long column; };",
        "std::optional<std::vector<Point>> diamond_perimeter(Point center, long long radius)",
        """if(radius<0||center.row<LLONG_MIN+radius||center.row>LLONG_MAX-radius||center.column<LLONG_MIN+radius||center.column>LLONG_MAX-radius)return std::nullopt;if(radius==0)return std::vector<Point>{center};std::vector<Point> out;Point p{center.row-radius,center.column};const std::array<Point,4> direction={Point{1,1},Point{1,-1},Point{-1,-1},Point{-1,1}};for(auto d:direction)for(long long i=0;i<radius;++i){out.push_back(p);p.row+=d.row;p.column+=d.column;}return out;""",
        """auto r=diamond_perimeter({0,0},1);assert(r&&r->size()==4&&r->at(0).row==-1&&r->at(1).column==1&&r->at(2).row==1);
    auto z=diamond_perimeter({2,3},0);assert(z&&z->size()==1&&z->at(0).column==3);
    assert(!diamond_perimeter({0,0},-1));
    assert(!diamond_perimeter({LLONG_MAX,0},1));""",
        ["radius is nonnegative", "radius zero is singleton", "start is top vertex", "clockwise traversal has four radius-length sides", "center plus radius arithmetic is checked"],
        "four directed diagonal walks around a Manhattan shell", ["perimeter", "coordinates", "diamond"],
    )
    add(
        "Diamond", "filled-diamond-count", "Filled diamond count",
        "Count all filled axis-aligned Manhattan diamonds made entirely of true cells in a rectangular Boolean grid. A radius-zero single true cell is a diamond; larger radii require every cell at distance at most radius.",
        "",
        "std::optional<std::size_t> count_filled_diamonds(const std::vector<std::vector<bool>>& grid)",
        """std::size_t columns=grid.empty()?0:grid[0].size();for(const auto&row:grid)if(row.size()!=columns)return std::nullopt;std::size_t count=0;for(std::size_t r=0;r<grid.size();++r)for(std::size_t c=0;c<columns;++c)for(std::size_t radius=0;;++radius){bool inside=true,all=true;for(long long dr=-static_cast<long long>(radius);dr<=static_cast<long long>(radius);++dr)for(long long dc=-static_cast<long long>(radius)+std::llabs(dr);dc<=static_cast<long long>(radius)-std::llabs(dr);++dc){long long rr=static_cast<long long>(r)+dr,cc=static_cast<long long>(c)+dc;if(rr<0||cc<0||rr>=static_cast<long long>(grid.size())||cc>=static_cast<long long>(columns)){inside=false;continue;}all=all&&grid[rr][cc];}if(!inside)break;if(all)++count;else break;}return count;""",
        """assert(count_filled_diamonds({{true}})==1);
    assert(count_filled_diamonds({{true,true},{true,true}})==4);
    assert(count_filled_diamonds({{true,false,true}})==2);
    assert(count_filled_diamonds({} )==0);
    assert(!count_filled_diamonds({{true},{true,false}}));""",
        ["grid is rectangular", "true cells form radius-zero diamonds", "a diamond must fit completely", "all interior cells are required", "count includes each center/radius pair"],
        "center-radius enumeration with complete Manhattan interior proof", ["filled-shape", "counting", "diamond"],
    )
    add(
        "Diamond", "nearest-mark-distance-field", "Nearest mark distance field",
        "Return the Manhattan distance from every cell in a rectangular grid to the nearest marked cell using multi-source traversal. When no marks exist return -1 everywhere; reject ragged grids.",
        "",
        "std::optional<std::vector<std::vector<int>>> nearest_mark_distances(const std::vector<std::vector<bool>>& marked)",
        """std::size_t rows=marked.size(),columns=rows?marked[0].size():0;for(const auto&row:marked)if(row.size()!=columns)return std::nullopt;std::vector<std::vector<int>> distance(rows,std::vector<int>(columns,-1));std::queue<std::pair<int,int>> q;for(std::size_t r=0;r<rows;++r)for(std::size_t c=0;c<columns;++c)if(marked[r][c]){distance[r][c]=0;q.push({static_cast<int>(r),static_cast<int>(c)});}const std::array<std::pair<int,int>,4> directions={{{1,0},{-1,0},{0,1},{0,-1}}};while(!q.empty()){auto[r,c]=q.front();q.pop();for(auto[dr,dc]:directions){int rr=r+dr,cc=c+dc;if(rr>=0&&cc>=0&&rr<static_cast<int>(rows)&&cc<static_cast<int>(columns)&&distance[rr][cc]<0){distance[rr][cc]=distance[r][c]+1;q.push({rr,cc});}}}return distance;""",
        """auto r=nearest_mark_distances({{false,true,false},{false,false,false}});assert(r&&r->at(0)==(std::vector<int>{1,0,1})&&r->at(1)==(std::vector<int>{2,1,2}));
    assert(nearest_mark_distances({})->empty());
    assert(nearest_mark_distances({{false}})->at(0).at(0)==-1);
    assert(!nearest_mark_distances({{true},{false,true}}));""",
        ["grid is rectangular", "marked cells have zero distance", "distance is Manhattan", "ties need no source identity", "no-source field is all -1"],
        "multi-source breadth-first distance propagation", ["distance-field", "multi-source-bfs", "diamond"],
    )

    add(
        "Grade School", "tie-aware-percentile-ranks", "Tie-aware percentile ranks",
        "Assign each student an exact percentile numerator over class size using midranks of equal integer scores. Students are uniquely named; output remains input order, and an empty class returns empty.",
        "struct StudentScore { std::string name; int score; };\nstruct Percentile { std::string name; long long numerator; long long denominator; };",
        "std::optional<std::vector<Percentile>> tie_aware_percentiles(const std::vector<StudentScore>& scores)",
        """std::set<std::string> names;for(const auto&s:scores)if(s.name.empty()||!names.insert(s.name).second)return std::nullopt;std::vector<int> ordered;for(const auto&s:scores)ordered.push_back(s.score);std::sort(ordered.begin(),ordered.end());std::vector<Percentile> out;for(const auto&s:scores){long long below=std::lower_bound(ordered.begin(),ordered.end(),s.score)-ordered.begin();long long equal=std::upper_bound(ordered.begin(),ordered.end(),s.score)-std::lower_bound(ordered.begin(),ordered.end(),s.score);long long numerator=2*below+equal;long long denominator=2*static_cast<long long>(scores.size());long long g=denominator?std::gcd(numerator,denominator):1;out.push_back({s.name,numerator/g,denominator?denominator/g:1});}return out;""",
        """auto r=tie_aware_percentiles({{"a",10},{"b",20},{"c",20}});assert(r&&r->at(0).numerator==1&&r->at(0).denominator==6&&r->at(1).numerator==2&&r->at(1).denominator==3);
    assert(tie_aware_percentiles({})->empty());
    assert(!tie_aware_percentiles({{"a",1},{"a",2}}));
    assert(!tie_aware_percentiles({{"",1}}));""",
        ["student names are unique nonempty", "midrank uses half the tied block", "fractions are reduced", "output preserves student order", "empty class returns empty"],
        "sorted score bounds converted to reduced exact midrank fractions", ["percentile", "ties", "rational"],
    )
    add(
        "Grade School", "attendance-streak-awards", "Attendance streak awards",
        "Given per-day attendance markers for uniquely named students, award one credit for every completed run of at least a threshold, counting disjoint maximal present runs. Reject invalid markers, nonpositive threshold, or duplicate names.",
        "struct AttendanceRow { std::string student; std::string markers; };",
        "std::optional<std::map<std::string,int>> attendance_streak_awards(const std::vector<AttendanceRow>& rows, int threshold)",
        """if(threshold<=0)return std::nullopt;std::map<std::string,int> out;for(const auto&row:rows){if(row.student.empty()||out.count(row.student)||!std::all_of(row.markers.begin(),row.markers.end(),[](char c){return c=='P'||c=='A';}))return std::nullopt;int awards=0,run=0;for(char c:row.markers){if(c=='P')++run;else{awards+=run>=threshold;run=0;}}awards+=run>=threshold;out[row.student]=awards;}return out;""",
        """auto r=attendance_streak_awards({{"ana","PPPAPPPP"},{"bo","AA"}},3);assert(r&&r->at("ana")==2&&r->at("bo")==0);
    assert(attendance_streak_awards({},1)->empty());
    assert(!attendance_streak_awards({},0));
    assert(!attendance_streak_awards({{"a","PX"}},2));
    assert(!attendance_streak_awards({{"a","P"},{"a","A"}},1));""",
        ["threshold is positive", "markers use P and A only", "student names are unique nonempty", "maximal present runs count once", "ending runs are finalized"],
        "single-pass maximal-run classification per student", ["attendance", "streak", "awards"],
    )
    add(
        "Grade School", "weighted-zscore-normalization", "Weighted z-score normalization",
        "Compute weighted population z-scores for integer grades with positive integer weights. Return exact zeroes when variance is zero; reject empty input, nonpositive weights, or non-finite derived values.",
        "struct WeightedGrade { int grade; int weight; };",
        "std::optional<std::vector<double>> weighted_grade_zscores(const std::vector<WeightedGrade>& grades)",
        """if(grades.empty())return std::nullopt;long double total=0,sum=0;for(auto g:grades){if(g.weight<=0)return std::nullopt;total+=g.weight;sum+=static_cast<long double>(g.grade)*g.weight;}long double mean=sum/total,variance=0;for(auto g:grades){long double d=g.grade-mean;variance+=d*d*g.weight;}variance/=total;std::vector<double> out;if(variance==0){out.assign(grades.size(),0);return out;}long double sigma=std::sqrt(variance);for(auto g:grades){double z=static_cast<double>((g.grade-mean)/sigma);if(!std::isfinite(z))return std::nullopt;out.push_back(z);}return out;""",
        """auto r=weighted_grade_zscores({{0,1},{2,1}});assert(r&&std::abs(r->at(0)+1)<1e-12&&std::abs(r->at(1)-1)<1e-12);
    auto z=weighted_grade_zscores({{7,3},{7,1}});assert(z&&z->at(0)==0&&z->at(1)==0);
    assert(!weighted_grade_zscores({}));
    assert(!weighted_grade_zscores({{1,0}}));""",
        ["input is nonempty", "weights are positive", "population variance uses total weight", "zero variance returns exact zeroes", "outputs follow input order"],
        "long-double weighted moments followed by stable normalization", ["zscore", "weighted", "calibration"],
    )

    add(
        "Kindergarten Garden", "greenhouse-band-violations", "Greenhouse band violations",
        "Compress a time series of integer greenhouse temperatures into maximal violation runs below a minimum or above a maximum. Readings inside the inclusive band split runs; reject an inverted band.",
        "enum class BandSide { below, above };\nstruct BandRun { std::size_t begin; std::size_t count; BandSide side; };",
        "std::optional<std::vector<BandRun>> greenhouse_band_violations(const std::vector<int>& readings, int minimum, int maximum)",
        """if(minimum>maximum)return std::nullopt;std::vector<BandRun> out;std::size_t i=0;while(i<readings.size()){if(readings[i]>=minimum&&readings[i]<=maximum){++i;continue;}BandSide side=readings[i]<minimum?BandSide::below:BandSide::above;std::size_t begin=i;while(i<readings.size()&&((side==BandSide::below&&readings[i]<minimum)||(side==BandSide::above&&readings[i]>maximum)))++i;out.push_back({begin,i-begin,side});}return out;""",
        """auto r=greenhouse_band_violations({1,2,5,9,10,4},3,8);assert(r&&r->size()==2&&r->at(0).count==2&&r->at(1).count==2&&r->at(1).begin==3);
    assert(greenhouse_band_violations({},0,0)->empty());
    assert(greenhouse_band_violations({3,4},3,4)->empty());
    assert(!greenhouse_band_violations({},5,4));""",
        ["band bounds are inclusive", "minimum does not exceed maximum", "below and above are separate run classes", "in-band readings split runs", "runs are maximal and ordered"],
        "classified maximal-run compression", ["greenhouse", "temperature", "run-length"],
    )
    add(
        "Kindergarten Garden", "germination-cohort-summary", "Germination cohort summary",
        "Group uniquely identified seeds by nonnegative germination day and return ascending day cohorts with stable seed ID order. Seeds that never germinated use no day and are counted separately.",
        "struct SeedResult { std::string id; std::optional<int> day; };\nstruct GerminationSummary { std::map<int,std::vector<std::string>> cohorts; std::size_t dormant; };",
        "std::optional<GerminationSummary> summarize_germination(const std::vector<SeedResult>& results)",
        """GerminationSummary out{};std::set<std::string> ids;for(const auto&r:results){if(r.id.empty()||!ids.insert(r.id).second||(r.day&&*r.day<0))return std::nullopt;if(r.day)out.cohorts[*r.day].push_back(r.id);else ++out.dormant;}return out;""",
        """auto r=summarize_germination({{"b",2},{"a",2},{"c",std::nullopt}});assert(r&&r->cohorts.at(2)==(std::vector<std::string>{"b","a"})&&r->dormant==1);
    auto e=summarize_germination({});assert(e&&e->cohorts.empty()&&e->dormant==0);
    assert(!summarize_germination({{"a",-1}}));
    assert(!summarize_germination({{"a",1},{"a",2}}));""",
        ["seed IDs are unique nonempty", "days are nonnegative", "dormant seeds have no day", "cohort keys ascend", "cohort members preserve input order"],
        "validated stable grouping by optional observation day", ["germination", "cohort", "grouping"],
    )
    add(
        "Kindergarten Garden", "pipe-tree-flow", "Pipe tree flow",
        "Propagate an integer water supply through a rooted pipe tree. Each node consumes a nonnegative amount, then divides the remainder among children by declared nonnegative weights, with leftover units assigned to lower child indices. Reject malformed trees, zero total child weight, or insufficient supply.",
        "struct PipeNode { int consumption; std::vector<std::pair<int,int>> children; };",
        "std::optional<std::vector<long long>> pipe_tree_deliveries(const std::vector<PipeNode>& nodes, int root, long long supply)",
        """if(supply<0||nodes.empty()||root<0||root>=static_cast<int>(nodes.size()))return std::nullopt;std::set<int> seen;std::vector<long long> delivered(nodes.size());std::function<bool(int,long long)> visit=[&](int node,long long amount){if(!seen.insert(node).second||nodes[node].consumption<0||amount<nodes[node].consumption)return false;delivered[node]=amount;long long remainder=amount-nodes[node].consumption,total_weight=0;auto children=nodes[node].children;std::sort(children.begin(),children.end());for(auto[child,weight]:children){if(child<0||child>=static_cast<int>(nodes.size())||weight<0)return false;total_weight+=weight;}if(!children.empty()&&total_weight==0)return false;long long assigned=0;std::vector<long long> shares;for(auto[child,weight]:children){(void)child;long long share=remainder*weight/total_weight;shares.push_back(share);assigned+=share;}for(std::size_t i=0;i<shares.size()&&assigned<remainder;++i,++assigned)++shares[i];for(std::size_t i=0;i<children.size();++i)if(!visit(children[i].first,shares[i]))return false;return true;};if(!visit(root,supply)||seen.size()!=nodes.size())return std::nullopt;return delivered;""",
        """auto r=pipe_tree_deliveries({{2,{{2,1},{1,1}}},{1,{}},{0,{}}},0,7);assert(r&&r->at(0)==7&&r->at(1)==3&&r->at(2)==2);
    assert(pipe_tree_deliveries({{0,{}}},0,0).value()==(std::vector<long long>{0}));
    assert(!pipe_tree_deliveries({{1,{}}},0,0));
    assert(!pipe_tree_deliveries({{0,{{0,1}}}},0,1));
    assert(!pipe_tree_deliveries({},0,0));""",
        ["supply and consumption are nonnegative", "tree is fully reachable without sharing", "child weights are nonnegative with positive total", "division remainder favors lower child index", "every node receives at least its consumption"],
        "recursive weighted integer flow with deterministic remainder allocation", ["pipe-tree", "flow", "garden"],
    )

    add(
        "Linked List", "polynomial-term-normalization", "Polynomial term normalization",
        "Normalize a linked-style polynomial term sequence by combining equal exponents, dropping zero coefficients, and returning terms in strictly descending exponent order. Reject negative exponents or coefficient-sum overflow.",
        "struct Term { long long coefficient; int exponent; };",
        "std::optional<std::vector<Term>> normalize_polynomial_terms(const std::vector<Term>& chain)",
        """std::map<int,long long,std::greater<int>> sums;for(auto term:chain){if(term.exponent<0)return std::nullopt;long long&sum=sums[term.exponent];if((term.coefficient>0&&sum>LLONG_MAX-term.coefficient)||(term.coefficient<0&&sum<LLONG_MIN-term.coefficient))return std::nullopt;sum+=term.coefficient;}std::vector<Term> out;for(auto item:sums)if(item.second!=0)out.push_back({item.second,item.first});return out;""",
        """auto r=normalize_polynomial_terms({{2,3},{4,1},{-2,3}});assert(r&&r->size()==1&&r->at(0).coefficient==4&&r->at(0).exponent==1);
    assert(normalize_polynomial_terms({})->empty());
    assert(!normalize_polynomial_terms({{1,-1}}));
    assert(!normalize_polynomial_terms({{LLONG_MAX,1},{1,1}}));""",
        ["exponents are nonnegative", "equal exponents combine", "zero totals disappear", "output exponent order descends", "coefficient addition is checked"],
        "checked ordered coefficient aggregation", ["polynomial", "term-chain", "normalization"],
    )
    add(
        "Linked List", "free-list-command-replay", "Free-list command replay",
        "Replay first-fit allocations and exact frees over a linear address arena. Free blocks coalesce, allocation IDs are unique, and frees must name active allocations. Return active allocations by ID and free blocks by address.",
        "struct MemoryCommand { bool allocate; std::string id; std::size_t size; };\nstruct MemoryState { std::map<std::string,std::pair<std::size_t,std::size_t>> active; std::map<std::size_t,std::size_t> free_blocks; };",
        "std::optional<MemoryState> replay_free_list(std::size_t arena_size, const std::vector<MemoryCommand>& commands)",
        """MemoryState state;state.free_blocks[0]=arena_size;for(const auto&command:commands){if(command.id.empty())return std::nullopt;if(command.allocate){if(command.size==0||state.active.count(command.id))return std::nullopt;auto chosen=state.free_blocks.end();for(auto it=state.free_blocks.begin();it!=state.free_blocks.end();++it)if(it->second>=command.size){chosen=it;break;}if(chosen==state.free_blocks.end())return std::nullopt;std::size_t begin=chosen->first,length=chosen->second;state.free_blocks.erase(chosen);if(length>command.size)state.free_blocks[begin+command.size]=length-command.size;state.active[command.id]={begin,command.size};}else{auto active=state.active.find(command.id);if(active==state.active.end()||command.size!=0)return std::nullopt;auto[begin,length]=active->second;state.active.erase(active);state.free_blocks[begin]=length;auto it=state.free_blocks.find(begin);if(it!=state.free_blocks.begin()){auto prev=std::prev(it);if(prev->first+prev->second==it->first){begin=prev->first;length+=prev->second;state.free_blocks.erase(prev);state.free_blocks.erase(it);it=state.free_blocks.emplace(begin,length).first;}}auto next=std::next(it);if(next!=state.free_blocks.end()&&it->first+it->second==next->first){it->second+=next->second;state.free_blocks.erase(next);}}}return state;""",
        """auto r=replay_free_list(10,{{true,"a",4},{true,"b",3},{false,"a",0}});assert(r&&r->active.at("b").first==4&&r->free_blocks.begin()->first==0&&r->free_blocks.begin()->second==4);
    auto e=replay_free_list(0,{});assert(e&&e->free_blocks.at(0)==0);
    assert(!replay_free_list(3,{{true,"a",4}}));
    assert(!replay_free_list(3,{{false,"a",0}}));
    assert(!replay_free_list(3,{{true,"a",0}}));""",
        ["allocation sizes are positive", "IDs are nonempty and active-unique", "allocation is first-fit by address", "free size field must be zero", "adjacent free blocks coalesce"],
        "ordered first-fit arena simulation with bidirectional coalescing", ["free-list", "allocator", "replay"],
    )
    add(
        "Linked List", "doubly-linked-integrity", "Doubly linked integrity",
        "Validate a fully reachable doubly linked chain and return its value order. Head previous and tail next are -1; every forward/back link must agree, indices are bounded, and no cycle or unreachable node is permitted.",
        "struct DoubleNode { int value; int previous; int next; };",
        "std::optional<std::vector<int>> validate_double_chain(const std::vector<DoubleNode>& nodes, int head)",
        """if(nodes.empty())return head==-1?std::optional<std::vector<int>>{std::vector<int>{}}:std::nullopt;if(head<0||head>=static_cast<int>(nodes.size())||nodes[head].previous!=-1)return std::nullopt;std::set<int> seen;std::vector<int> out;int previous=-1;for(int current=head;current!=-1;current=nodes[current].next){if(current<0||current>=static_cast<int>(nodes.size())||!seen.insert(current).second||nodes[current].previous!=previous)return std::nullopt;out.push_back(nodes[current].value);int next=nodes[current].next;if(next!=-1&&(next<0||next>=static_cast<int>(nodes.size())||nodes[next].previous!=current))return std::nullopt;previous=current;}if(seen.size()!=nodes.size())return std::nullopt;return out;""",
        """assert(validate_double_chain({{1,-1,1},{2,0,-1}},0).value()==(std::vector<int>{1,2}));
    assert(validate_double_chain({},-1)->empty());
    assert(!validate_double_chain({{1,0,-1}},0));
    assert(!validate_double_chain({{1,-1,0}},0));
    assert(!validate_double_chain({{1,-1,-1},{2,-1,-1}},0));""",
        ["empty chain uses head -1", "head previous is -1", "forward and backward links agree", "all nodes are reached once", "tail next is -1"],
        "forward traversal with local backlink and global reachability proof", ["doubly-linked", "integrity", "validation"],
    )

    add(
        "Parallel Letter Frequency", "parallel-word-length-histogram", "Parallel word length histogram",
        "Count ASCII-letter run lengths across texts using bounded asynchronous shards. Runs do not cross text boundaries; nonletters delimit runs. Merge into an ascending length histogram and reject zero workers.",
        "",
        "std::optional<std::map<std::size_t,std::size_t>> parallel_word_length_histogram(const std::vector<std::string>& texts, std::size_t workers)",
        """if(workers==0)return std::nullopt;workers=std::min(workers,std::max<std::size_t>(1,texts.size()));std::vector<std::future<std::map<std::size_t,std::size_t>>> jobs;for(std::size_t w=0;w<workers;++w)jobs.push_back(std::async(std::launch::async,[&,w]{std::map<std::size_t,std::size_t> local;for(std::size_t t=w;t<texts.size();t+=workers){std::size_t run=0;for(unsigned char c:texts[t]){if(c<128&&std::isalpha(c))++run;else if(run){++local[run];run=0;}}if(run)++local[run];}return local;}));std::map<std::size_t,std::size_t> out;for(auto&job:jobs)for(auto item:job.get())out[item.first]+=item.second;return out;""",
        """const std::vector<std::string> documents{"A-rose has 4 petals", "violets_are_blue", "X"};
    const std::map<std::size_t,std::size_t> expected{{1,2},{3,2},{4,2},{6,1},{7,1}};
    for(std::size_t worker_count:std::array<std::size_t,3>{1,2,11}){
        const auto observed=parallel_word_length_histogram(documents,worker_count);
        assert(observed.has_value());
        assert(*observed==expected);
    }
    const auto delimiters=parallel_word_length_histogram({"9--7", "..."},5);
    assert(delimiters&&delimiters->empty());
    const auto empty_batch=parallel_word_length_histogram({},4);
    assert(empty_batch&&empty_batch->empty());
    assert(!parallel_word_length_histogram(documents,0).has_value());""",
        ["worker count is positive", "only ASCII letters join runs", "runs reset at text boundaries", "workers are bounded by useful input", "merge ordering is deterministic"],
        "strided asynchronous run histograms with ordered reduction", ["parallel", "word-length", "histogram"],
    )
    add(
        "Parallel Letter Frequency", "parallel-prefix-xor", "Parallel prefix XOR",
        "Compute inclusive prefix XOR over byte blocks using contiguous asynchronous shard summaries, then offset each local prefix by the XOR of all prior shards. Reject zero workers and preserve exact input length.",
        "",
        "std::optional<std::vector<unsigned char>> parallel_prefix_xor(const std::vector<unsigned char>& bytes, std::size_t workers)",
        """if(workers==0)return std::nullopt;workers=std::min(workers,std::max<std::size_t>(1,bytes.size()));struct Part{std::size_t begin;std::vector<unsigned char> prefix;unsigned char total;};std::vector<std::future<Part>> jobs;for(std::size_t w=0;w<workers;++w){std::size_t lo=bytes.size()*w/workers,hi=bytes.size()*(w+1)/workers;jobs.push_back(std::async(std::launch::async,[&,lo,hi]{Part p{lo,{},0};for(std::size_t i=lo;i<hi;++i){p.total^=bytes[i];p.prefix.push_back(p.total);}return p;}));}std::vector<unsigned char> out(bytes.size());unsigned char offset=0;for(auto&job:jobs){Part p=job.get();for(std::size_t i=0;i<p.prefix.size();++i)out[p.begin+i]=static_cast<unsigned char>(p.prefix[i]^offset);offset^=p.total;}return out;""",
        """assert(parallel_prefix_xor({1,2,3,4},2).value()==(std::vector<unsigned char>{1,3,0,4}));
    assert(parallel_prefix_xor({},4)->empty());
    assert(parallel_prefix_xor({7},9).value()==(std::vector<unsigned char>{7}));
    assert(!parallel_prefix_xor({},0));""",
        ["workers are positive", "shards are contiguous", "local prefixes are inclusive", "prior shard totals offset later shards", "empty input returns empty"],
        "two-phase contiguous-shard scan with deterministic offsets", ["parallel", "prefix-scan", "xor"],
    )
    add(
        "Parallel Letter Frequency", "parallel-palindrome-token-count", "Parallel palindrome token count",
        "Count case-insensitive ASCII-letter tokens that are palindromes of at least a minimum length, processing texts asynchronously. Nonletters delimit tokens, text boundaries reset state, and zero workers or zero minimum reject.",
        "",
        "std::optional<std::size_t> parallel_palindrome_token_count(const std::vector<std::string>& texts, std::size_t workers, std::size_t minimum_length)",
        """if(workers==0||minimum_length==0)return std::nullopt;workers=std::min(workers,std::max<std::size_t>(1,texts.size()));std::vector<std::future<std::size_t>> jobs;for(std::size_t w=0;w<workers;++w)jobs.push_back(std::async(std::launch::async,[&,w]{std::size_t count=0;for(std::size_t t=w;t<texts.size();t+=workers){std::string token;auto finish=[&]{if(token.size()>=minimum_length&&std::equal(token.begin(),token.begin()+static_cast<std::ptrdiff_t>(token.size()/2),token.rbegin()))++count;token.clear();};for(unsigned char c:texts[t])if(c<128&&std::isalpha(c))token.push_back(static_cast<char>(std::tolower(c)));else finish();finish();}return count;}));std::size_t total=0;for(auto&job:jobs)total+=job.get();return total;""",
        """assert(parallel_palindrome_token_count({"Level kayak no","abba!x"},2,4)==3);
    assert(parallel_palindrome_token_count({},1,1)==0);
    assert(!parallel_palindrome_token_count({},0,1));
    assert(!parallel_palindrome_token_count({},1,0));""",
        ["workers and minimum length are positive", "ASCII letters form tokens", "case is ignored", "tokens do not cross texts", "each qualifying token counts once"],
        "asynchronous tokenization with local palindrome predicates", ["parallel", "palindrome", "token"],
    )

    add(
        "Phone Number", "extension-grammar-parser", "Extension grammar parser",
        "Parse a domestic digit number followed optionally by exactly one extension introduced by x, ext, or extension with surrounding spaces. Base has 7 through 15 digits; extension has 1 through 6 digits. Return canonical digit strings.",
        "struct ParsedExtension { std::string base; std::optional<std::string> extension; };",
        "std::optional<ParsedExtension> parse_phone_extension(std::string_view text)",
        """std::string compact;for(char c:text)if(c!=' '&&c!='-'&&c!='('&&c!=')')compact.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(c))));std::size_t split=std::string::npos,marker=0;auto full=compact.find("extension");auto short_marker=compact.find("ext");auto x=compact.find('x');if(full!=std::string::npos){split=full;marker=9;}else if(short_marker!=std::string::npos){split=short_marker;marker=3;}else if(x!=std::string::npos){split=x;marker=1;}std::string base=split==std::string::npos?compact:compact.substr(0,split),ext=split==std::string::npos?std::string{}:compact.substr(split+marker);auto digits=[](const std::string&s){return std::all_of(s.begin(),s.end(),[](unsigned char c){return std::isdigit(c);});};if(base.size()<7||base.size()>15||!digits(base)||(split!=std::string::npos&&(ext.empty()||ext.size()>6||!digits(ext))))return std::nullopt;return ParsedExtension{base,split==std::string::npos?std::optional<std::string>{}:std::optional<std::string>{ext}};""",
        """auto r=parse_phone_extension("(212)555-0100 ext 42");assert(r&&r->base=="2125550100"&&r->extension=="42");
    auto b=parse_phone_extension("1234567");assert(b&&!b->extension);
    assert(!parse_phone_extension("123 x 4"));
    assert(!parse_phone_extension("1234567 ext"));
    assert(!parse_phone_extension("1234567x1x2"));""",
        ["defined separators are ignored", "base length is 7 through 15", "extension marker occurs at most once", "extension length is 1 through 6", "canonical output contains digits only"],
        "marker-aware normalization with strict base/extension grammar", ["extension", "parser", "phone"],
    )
    add(
        "Phone Number", "emergency-prefix-routing", "Emergency prefix routing",
        "Route a digit number by the longest matching emergency prefix. Prefix records are unique digit strings with nonempty destinations; ties cannot occur. Return no route when no prefix matches and reject malformed tables or numbers.",
        "struct PrefixRoute { std::string prefix; std::string destination; };",
        "std::optional<std::optional<std::string>> route_emergency_prefix(std::string_view number, const std::vector<PrefixRoute>& routes)",
        """auto digit_string=[](std::string_view s){return !s.empty()&&std::all_of(s.begin(),s.end(),[](unsigned char c){return std::isdigit(c);});};if(!digit_string(number))return std::nullopt;std::set<std::string> prefixes;std::optional<std::string> best;std::size_t best_length=0;for(const auto&r:routes){if(!digit_string(r.prefix)||r.destination.empty()||!prefixes.insert(r.prefix).second)return std::nullopt;if(number.substr(0,r.prefix.size())==r.prefix&&r.prefix.size()>best_length){best=r.destination;best_length=r.prefix.size();}}return best;""",
        """auto r=route_emergency_prefix("91123",{{"9","local"},{"911","emergency"}});assert(r&&*r&&**r=="emergency");
    auto none=route_emergency_prefix("123",{{"9","x"}});assert(none&&!*none);
    assert(!route_emergency_prefix("12x",{}));
    assert(!route_emergency_prefix("123",{{"1","a"},{"1","b"}}));""",
        ["number and prefixes are nonempty digits", "prefixes are unique", "destinations are nonempty", "longest match wins", "no match is distinct from malformed input"],
        "validated longest-prefix selection", ["prefix", "routing", "phone"],
    )
    add(
        "Phone Number", "call-burst-detector", "Call burst detector",
        "For timestamped calls sorted by second, return maximal runs to the same digit-only number where consecutive calls are separated by at most a gap. Only runs meeting a minimum call count are returned; reject malformed calls or parameters.",
        "struct CallEvent { int second; std::string number; };\nstruct CallBurst { std::string number; int begin_second; int end_second; std::size_t count; };",
        "std::optional<std::vector<CallBurst>> detect_call_bursts(const std::vector<CallEvent>& calls, int maximum_gap, std::size_t minimum_calls)",
        """if(maximum_gap<0||minimum_calls==0)return std::nullopt;int previous=-1;for(const auto&c:calls){if(c.second<0||c.second<previous||c.number.empty()||!std::all_of(c.number.begin(),c.number.end(),[](unsigned char x){return std::isdigit(x);}))return std::nullopt;previous=c.second;}std::vector<CallBurst> out;std::size_t i=0;while(i<calls.size()){std::size_t begin=i;++i;while(i<calls.size()&&calls[i].number==calls[begin].number&&calls[i].second-calls[i-1].second<=maximum_gap)++i;if(i-begin>=minimum_calls)out.push_back({calls[begin].number,calls[begin].second,calls[i-1].second,i-begin});}return out;""",
        """auto r=detect_call_bursts({{1,"12"},{3,"12"},{10,"12"},{11,"34"},{12,"34"}},3,2);assert(r&&r->size()==2&&r->at(0).count==2&&r->at(1).number=="34");
    assert(detect_call_bursts({},0,1)->empty());
    assert(!detect_call_bursts({},-1,1));
    assert(!detect_call_bursts({},1,0));
    assert(!detect_call_bursts({{2,"1"},{1,"1"}},2,1));""",
        ["timestamps are nonnegative sorted", "numbers are digit-only", "same-number adjacency is required", "gap is inclusive", "runs are maximal in input order"],
        "classified adjacent-run compression with time-gap constraint", ["call-log", "burst", "run"],
    )

    add(
        "Spiral Matrix", "ulam-spiral-coordinate", "Ulam spiral coordinate",
        "Map a positive Ulam spiral label to Cartesian coordinates where 1 is origin, 2 is right, and labels then spiral counterclockwise upward. Reject zero or labels above an inclusive caller bound.",
        "struct Coordinate { long long x; long long y; };",
        "std::optional<Coordinate> ulam_coordinate(std::uint64_t label, std::uint64_t maximum)",
        """if(label==0||label>maximum)return std::nullopt;if(label==1)return Coordinate{0,0};std::uint64_t side=static_cast<std::uint64_t>(std::ceil(std::sqrt(static_cast<long double>(label))));if(side%2==0)++side;std::uint64_t radius=(side-1)/2,max_value=side*side,offset=max_value-label,edge=side-1;long long r=static_cast<long long>(radius),x=r,y=-r;if(offset<edge)x-=static_cast<long long>(offset);else if(offset<2*edge){x=-r;y+=static_cast<long long>(offset-edge);}else if(offset<3*edge){x=-r+static_cast<long long>(offset-2*edge);y=r;}else{x=r;y=r-static_cast<long long>(offset-3*edge);}return Coordinate{x,y};""",
        """auto a=ulam_coordinate(1,25);assert(a&&a->x==0&&a->y==0);auto b=ulam_coordinate(2,25);assert(b&&b->x==1&&b->y==0);auto c=ulam_coordinate(9,25);assert(c&&c->x==1&&c->y==-1);auto d=ulam_coordinate(10,25);assert(d&&d->x==2&&d->y==-1);
    assert(!ulam_coordinate(0,9));
    assert(!ulam_coordinate(10,9));""",
        ["labels are positive", "maximum is inclusive", "orientation fixes label two to the right", "odd-square corners anchor rings", "coordinates are signed"],
        "odd-square ring localization and edge offset decoding", ["ulam", "spiral", "coordinate"],
    )
    add(
        "Spiral Matrix", "matrix-peel-layer-sums", "Matrix peel layer sums",
        "Return sums of successive rectangular perimeter layers from outside inward. Each cell contributes exactly once, including single-row or single-column final layers. Reject ragged matrices or sum overflow.",
        "",
        "std::optional<std::vector<long long>> peel_layer_sums(const std::vector<std::vector<int>>& matrix)",
        """std::size_t rows=matrix.size(),columns=rows?matrix[0].size():0;for(const auto&row:matrix)if(row.size()!=columns)return std::nullopt;std::vector<long long> out;std::size_t top=0,left=0,bottom=rows,right=columns;while(top<bottom&&left<right){long long sum=0;auto add=[&](int v){if((v>0&&sum>LLONG_MAX-v)||(v<0&&sum<LLONG_MIN-v))return false;sum+=v;return true;};for(std::size_t c=left;c<right;++c)if(!add(matrix[top][c]))return std::nullopt;for(std::size_t r=top+1;r<bottom;++r)if(!add(matrix[r][right-1]))return std::nullopt;if(bottom-top>1)for(std::size_t c=right-1;c-->left;)if(!add(matrix[bottom-1][c]))return std::nullopt;if(right-left>1)for(std::size_t r=bottom-1;r-->top+1;)if(!add(matrix[r][left]))return std::nullopt;out.push_back(sum);++top;++left;--bottom;--right;}return out;""",
        """const std::vector<std::vector<std::vector<int>>> matrices{
        {{2,-1,4,8},{3,5,7,9},{6,0,1,2}},
        {{-4},{10},{3},{-2}},
        {{}}
    };
    const std::vector<std::vector<long long>> layers{{34,12},{7},{}};
    for(std::size_t index=0;index<matrices.size();++index){
        const auto actual=peel_layer_sums(matrices[index]);
        assert(actual.has_value());
        assert(*actual==layers[index]);
    }
    const std::vector<std::vector<int>> ragged{{1,2},{3}};
    assert(!peel_layer_sums(ragged).has_value());
    assert(peel_layer_sums({})->empty());""",
        ["matrix is rectangular", "layers proceed outside inward", "corners count once", "single row/column layers count every cell", "layer sums are checked"],
        "boundary-layer enumeration with degeneracy guards", ["peel", "layers", "matrix"],
    )
    add(
        "Spiral Matrix", "spiral-direction-runs", "Spiral direction runs",
        "Encode a complete clockwise rectangular spiral traversal as direction/count runs starting at top-left. The first cell is implicit, zero-area shapes return no runs, and cell count is bounded by a caller maximum.",
        "struct DirectionRun { char direction; std::size_t count; };",
        "std::optional<std::vector<DirectionRun>> spiral_direction_runs(std::size_t rows, std::size_t columns, std::size_t maximum_cells)",
        """if(columns&&rows>maximum_cells/columns)return std::nullopt;std::size_t cells=rows*columns;if(cells>maximum_cells)return std::nullopt;std::vector<DirectionRun> out;if(cells<=1)return out;std::size_t top=0,left=0,bottom=rows,right=columns;auto emit=[&](char d,std::size_t count){if(count)out.push_back({d,count});};while(top<bottom&&left<right){if(top==0)emit('R',right-left-1);else emit('R',right-left);++top;if(top<bottom)emit('D',bottom-top);if(left<right)--right;if(top<bottom&&left<right){emit('L',right-left);--bottom;}if(top<bottom&&left<right){emit('U',bottom-top);++left;}}std::size_t moved=0;for(auto run:out)moved+=run.count;if(moved!=cells-1)return std::nullopt;return out;""",
        """auto r=spiral_direction_runs(2,3,6);assert(r&&r->size()==3&&r->at(0).direction=='R'&&r->at(0).count==2&&r->at(1).direction=='D'&&r->at(2).direction=='L');
    assert(spiral_direction_runs(1,1,1)->empty());
    assert(spiral_direction_runs(0,9,0)->empty());
    assert(!spiral_direction_runs(3,3,8));""",
        ["top-left starting cell is implicit", "directions are R D L U", "zero area and singleton have no moves", "run counts are positive", "sum of counts is cells minus one"],
        "boundary shrinkage emitted directly as canonical direction runs", ["spiral", "run-length", "near-correct"],
    )

    add(
        "Sublist", "subsequence-embedding-count", "Subsequence embedding count",
        "Count distinct index embeddings of a pattern as a not-necessarily-contiguous subsequence of a haystack, up to an inclusive maximum. Empty pattern has one embedding; reject when the exact count exceeds the limit.",
        "",
        "std::optional<std::uint64_t> subsequence_embedding_count(const std::vector<int>& haystack, const std::vector<int>& pattern, std::uint64_t maximum)",
        """std::vector<std::uint64_t> dp(pattern.size()+1);dp[0]=1;for(int value:haystack)for(std::size_t j=pattern.size();j>0;--j)if(value==pattern[j-1]){if(dp[j]>maximum-dp[j-1])return std::nullopt;dp[j]+=dp[j-1];}return dp.back();""",
        """assert(subsequence_embedding_count({1,1,1},{1,1},3)==3);
    assert(subsequence_embedding_count({1,2,3},{1,3},1)==1);
    assert(subsequence_embedding_count({}, {}, 1)==1);
    assert(subsequence_embedding_count({}, {1}, 0)==0);
    assert(!subsequence_embedding_count({1,1,1},{1},2));""",
        ["empty pattern has one embedding", "nonempty pattern in empty haystack has zero", "indices increase strictly", "equal values may yield multiple embeddings", "count above maximum rejects"],
        "reverse-updated exact subsequence dynamic programming", ["subsequence", "count", "dynamic-programming"],
    )
    add(
        "Sublist", "interval-list-containment", "Interval list containment",
        "Classify two canonical unions of integer half-open intervals as equal, first-contained, second-contained, overlapping, or disjoint. Each list is sorted, nonempty intervals do not overlap or touch, and malformed lists reject.",
        "struct IntInterval { int begin; int end; };\nenum class UnionRelation { equal, first_contained, second_contained, overlapping, disjoint };",
        "std::optional<UnionRelation> interval_union_relation(const std::vector<IntInterval>& first, const std::vector<IntInterval>& second)",
        """auto valid=[](const std::vector<IntInterval>&v){for(std::size_t i=0;i<v.size();++i)if(v[i].begin>=v[i].end||(i&&v[i-1].end>=v[i].begin))return false;return true;};if(!valid(first)||!valid(second))return std::nullopt;auto contained=[](const auto&a,const auto&b){std::size_t j=0;for(auto x:a){while(j<b.size()&&b[j].end<=x.begin)++j;if(j==b.size()||b[j].begin>x.begin||b[j].end<x.end)return false;}return true;};bool ab=contained(first,second),ba=contained(second,first);if(ab&&ba)return UnionRelation::equal;if(ab)return UnionRelation::first_contained;if(ba)return UnionRelation::second_contained;std::size_t i=0,j=0;while(i<first.size()&&j<second.size()){if(std::max(first[i].begin,second[j].begin)<std::min(first[i].end,second[j].end))return UnionRelation::overlapping;if(first[i].end<second[j].end)++i;else ++j;}return UnionRelation::disjoint;""",
        """assert(interval_union_relation({{1,2}},{{0,3}})==UnionRelation::first_contained);
    assert(interval_union_relation({{1,3}},{{2,4}})==UnionRelation::overlapping);
    assert(interval_union_relation({},{} )==UnionRelation::equal);
    assert(interval_union_relation({{1,2}},{{2,3}})==UnionRelation::disjoint);
    assert(!interval_union_relation({{1,2},{2,3}},{}));""",
        ["intervals are nonempty half-open", "each union is sorted with positive gaps", "empty unions compare equal", "touching is disjoint", "containment is set containment across union components"],
        "canonical-union containment scans plus overlap merge scan", ["interval-union", "relation", "containment"],
    )
    add(
        "Sublist", "longest-common-contiguous-run", "Longest common contiguous run",
        "Return the longest exactly equal contiguous run shared by two integer sequences. Ties prefer the earlier start in the first sequence, then earlier start in the second. Empty result uses count zero and starts zero.",
        "struct CommonRun { std::size_t first_begin; std::size_t second_begin; std::size_t count; };",
        "CommonRun longest_common_run(const std::vector<int>& first, const std::vector<int>& second)",
        """CommonRun best{0,0,0};std::vector<std::size_t> previous(second.size()+1),current(second.size()+1);for(std::size_t i=1;i<=first.size();++i){for(std::size_t j=1;j<=second.size();++j)if(first[i-1]==second[j-1]){current[j]=previous[j-1]+1;CommonRun candidate{i-current[j],j-current[j],current[j]};if(candidate.count>best.count||(candidate.count==best.count&&std::tie(candidate.first_begin,candidate.second_begin)<std::tie(best.first_begin,best.second_begin)))best=candidate;}else current[j]=0;previous.swap(current);std::fill(current.begin(),current.end(),0);}return best;""",
        """auto r=longest_common_run({1,2,3,2,3},{9,2,3});assert(r.count==2&&r.first_begin==1&&r.second_begin==1);
    auto e=longest_common_run({},{});assert(e.count==0&&e.first_begin==0&&e.second_begin==0);
    auto n=longest_common_run({1},{2});assert(n.count==0);
    auto t=longest_common_run({1,2,1,2},{1,2});assert(t.first_begin==0);""",
        ["matching is exact", "run is contiguous in both inputs", "maximum length wins", "ties use first then second origin", "no match returns canonical zero run"],
        "rolling-row longest-common-substring dynamic programming", ["contiguous", "common-run", "dynamic-programming"],
    )

    add(
        "Yacht", "straight-completion-counts", "Straight completion counts",
        "For a partial hand of distinct dice, count final sorted hands that form each possible straight of a requested length after adding exactly missing_count dice. Faces range one through sides. Reject duplicates, invalid faces, or inconsistent hand size.",
        "",
        "std::optional<std::map<int,std::uint64_t>> straight_completion_counts(const std::vector<int>& held, int sides, int straight_length, int missing_count)",
        """if(sides<=0||straight_length<=0||straight_length>sides||missing_count<0||held.size()+static_cast<std::size_t>(missing_count)!=static_cast<std::size_t>(straight_length))return std::nullopt;std::set<int> unique;for(int d:held)if(d<1||d>sides||!unique.insert(d).second)return std::nullopt;std::map<int,std::uint64_t> out;for(int start=1;start+straight_length-1<=sides;++start){int present=0;for(int d:held)present+=d>=start&&d<start+straight_length;if(present==static_cast<int>(held.size()))out[start]=present+missing_count==straight_length?1:0;}return out;""",
        """auto r=straight_completion_counts({2,4},6,4,2);assert(r&&r->at(1)==1&&r->at(2)==1);
    assert(straight_completion_counts({},6,3,3)->size()==4);
    assert(!straight_completion_counts({1,1},6,3,1));
    assert(!straight_completion_counts({7},6,2,1));
    assert(!straight_completion_counts({1},6,3,1));""",
        ["faces are distinct and in range", "straight length is bounded by sides", "held plus missing equals straight length", "every containing straight start is returned", "counts represent sorted final hands"],
        "enumerate containing straight intervals under exact hand-size constraints", ["straight", "dice", "completion"],
    )
    add(
        "Yacht", "dice-multiset-rank", "Dice multiset rank",
        "Rank a sorted nondecreasing dice multiset among all same-sized multisets over faces one through sides in lexicographic order, starting at zero. Reject invalid order or faces and checked combinatorial overflow.",
        "",
        "std::optional<std::uint64_t> dice_multiset_rank(const std::vector<int>& dice, int sides)",
        """if(sides<=0||!std::is_sorted(dice.begin(),dice.end()))return std::nullopt;for(int d:dice)if(d<1||d>sides)return std::nullopt;auto choose=[](std::uint64_t n,std::uint64_t k)->std::optional<std::uint64_t>{k=std::min(k,n-k);std::uint64_t value=1;for(std::uint64_t i=1;i<=k;++i){std::uint64_t numerator=n-k+i,denominator=i;auto divisor=std::gcd(numerator,denominator);numerator/=divisor;denominator/=divisor;divisor=std::gcd(value,denominator);value/=divisor;denominator/=divisor;if(denominator!=1||(numerator!=0&&value>std::numeric_limits<std::uint64_t>::max()/numerator))return std::nullopt;value*=numerator;}return value;};std::uint64_t rank=0;int minimum=1;for(std::size_t i=0;i<dice.size();++i){for(int face=minimum;face<dice[i];++face){auto count=choose(static_cast<std::uint64_t>(sides-face+dice.size()-i-1),dice.size()-i-1);if(!count||rank>std::numeric_limits<std::uint64_t>::max()-*count)return std::nullopt;rank+=*count;}minimum=dice[i];}return rank;""",
        """assert(dice_multiset_rank({1,1},3)==0);
    assert(dice_multiset_rank({1,2},3)==1);
    assert(dice_multiset_rank({2,2},3)==3);
    assert(dice_multiset_rank({},6)==0);
    assert(!dice_multiset_rank({2,1},6));""",
        ["sides is positive", "dice are sorted nondecreasing", "faces are in range", "rank is zero-based lexicographic", "binomial and rank arithmetic are checked"],
        "combinatorial prefix counting over multiset lexicographic blocks", ["dice", "multiset", "near-correct"],
    )
    add(
        "Yacht", "single-reroll-state-graph", "Single reroll state graph",
        "Build the sorted unique multiset states reachable by rerolling exactly one die in a sorted hand to any face. The original state is included when a reroll repeats the same face. Reject invalid hands or sides.",
        "",
        "std::optional<std::vector<std::vector<int>>> single_reroll_states(const std::vector<int>& sorted_hand, int sides)",
        """if(sides<=0||!std::is_sorted(sorted_hand.begin(),sorted_hand.end()))return std::nullopt;for(int d:sorted_hand)if(d<1||d>sides)return std::nullopt;std::set<std::vector<int>> states;if(sorted_hand.empty())return std::vector<std::vector<int>>{};for(std::size_t i=0;i<sorted_hand.size();++i)for(int face=1;face<=sides;++face){auto state=sorted_hand;state[i]=face;std::sort(state.begin(),state.end());states.insert(std::move(state));}return std::vector<std::vector<int>>(states.begin(),states.end());""",
        """auto r=single_reroll_states({1,1},3);assert(r&&r->size()==3&&r->front()==(std::vector<int>{1,1})&&r->back()==(std::vector<int>{1,3}));
    assert(single_reroll_states({},6)->empty());
    assert(!single_reroll_states({2,1},6));
    assert(!single_reroll_states({0},6));
    assert(!single_reroll_states({},0));""",
        ["hand is sorted and faces valid", "exactly one position is chosen", "replacement spans every face", "duplicate states collapse", "states sort lexicographically"],
        "exhaustive one-position substitution into a canonical multiset state set", ["dice", "state-graph", "reroll"],
    )

    add(
        "Zebra Puzzle", "all-different-matching-count", "All-different matching count",
        "Count assignments of one distinct value to each variable from its sorted candidate set, up to an inclusive maximum. Candidate values lie in a declared range; empty variable list has one assignment.",
        "",
        "std::optional<std::uint64_t> all_different_assignment_count(const std::vector<std::vector<int>>& candidates, int value_count, std::uint64_t maximum)",
        """if(value_count<0)return std::nullopt;for(const auto&row:candidates)if(!std::is_sorted(row.begin(),row.end())||std::adjacent_find(row.begin(),row.end())!=row.end()||!std::all_of(row.begin(),row.end(),[&](int v){return v>=0&&v<value_count;}))return std::nullopt;std::vector<bool> used(static_cast<std::size_t>(value_count));std::uint64_t count=0;std::function<bool(std::size_t)> rec=[&](std::size_t i){if(i==candidates.size())return ++count<=maximum;for(int v:candidates[i])if(!used[v]){used[v]=true;if(!rec(i+1))return false;used[v]=false;}return true;};if(!rec(0))return std::nullopt;return count;""",
        """const std::vector<std::vector<int>> cycle{{0,1},{1,2},{0,2}};
    const auto full_count=all_different_assignment_count(cycle,3,20);
    assert(full_count.has_value());
    assert(*full_count==2);
    std::uint64_t singleton_product=1;
    for(int value:std::array<int,4>{0,1,2,3}){
        const auto one=all_different_assignment_count({{value}},4,1);
        assert(one&&*one==1);
        singleton_product*=*one;
    }
    assert(singleton_product==1);
    const auto vacant=all_different_assignment_count({},0,1);
    assert(vacant&&*vacant==1);
    const auto impossible=all_different_assignment_count({{}, {0}},1,9);
    assert(impossible&&*impossible==0);
    assert(!all_different_assignment_count({{2,1}},3,8).has_value());
    assert(!all_different_assignment_count(cycle,3,1).has_value());""",
        ["value count is nonnegative", "candidate rows are sorted unique in range", "values cannot repeat across variables", "empty variable set has one assignment", "count above maximum rejects"],
        "bounded backtracking matching count with a used-value bitmap", ["all-different", "matching", "count"],
    )
    add(
        "Zebra Puzzle", "permutation-clue-partitions", "Permutation clue partitions",
        "Partition all permutations of sorted unique labels by the truth vector of declared before-clues and return truth-vector bucket sizes. Reject unknown, self, or duplicate clues and enforce a factorial state bound.",
        "struct OrderConstraint { std::string first; std::string second; };",
        "std::optional<std::map<std::string,std::uint64_t>> permutation_clue_partitions(const std::vector<std::string>& labels, const std::vector<OrderConstraint>& clues, std::uint64_t maximum_permutations)",
        """if(!std::is_sorted(labels.begin(),labels.end())||std::adjacent_find(labels.begin(),labels.end())!=labels.end()||std::find(labels.begin(),labels.end(),\"\")!=labels.end())return std::nullopt;std::set<std::pair<std::string,std::string>> unique;for(const auto&c:clues)if(c.first==c.second||!std::binary_search(labels.begin(),labels.end(),c.first)||!std::binary_search(labels.begin(),labels.end(),c.second)||!unique.insert({c.first,c.second}).second)return std::nullopt;std::uint64_t factorial=1;for(std::uint64_t i=2;i<=labels.size();++i){if(factorial>maximum_permutations/i)return std::nullopt;factorial*=i;}std::map<std::string,std::uint64_t> out;auto permutation=labels;do{std::map<std::string,std::size_t> position;for(std::size_t i=0;i<permutation.size();++i)position[permutation[i]]=i;std::string key;for(const auto&c:clues)key.push_back(position[c.first]<position[c.second]?'1':'0');++out[key];}while(std::next_permutation(permutation.begin(),permutation.end()));return out;""",
        """auto r=permutation_clue_partitions({"a","b"},{{"a","b"}},2);assert(r&&r->at("0")==1&&r->at("1")==1);
    assert(permutation_clue_partitions({}, {}, 1)->at("")==1);
    assert(!permutation_clue_partitions({"b","a"},{},2));
    assert(!permutation_clue_partitions({"a"},{{"a","a"}},1));
    assert(!permutation_clue_partitions({"a","b","c"},{},5));""",
        ["labels are sorted unique nonempty strings", "clues are unique known non-self pairs", "truth vector follows clue order", "all permutations are represented", "factorial bound is checked before enumeration"],
        "exhaustive permutation truth-vector bucketing", ["permutation", "clue-partition", "truth-vector"],
    )
    add(
        "Zebra Puzzle", "minimal-contradiction-prefix", "Minimal contradiction prefix",
        "Find the shortest prefix of equality/inequality clues that makes a label system inconsistent. Equality merges components; inequality conflicts when endpoints are already equal. Return no prefix if all clues are consistent and reject malformed labels or clues.",
        "struct EqualityClue { std::string first; std::string second; bool equal; };",
        "std::optional<std::optional<std::size_t>> minimal_contradiction_prefix(const std::vector<std::string>& labels, const std::vector<EqualityClue>& clues)",
        """if(!std::is_sorted(labels.begin(),labels.end())||std::adjacent_find(labels.begin(),labels.end())!=labels.end()||std::find(labels.begin(),labels.end(),\"\")!=labels.end())return std::nullopt;std::vector<int> parent(labels.size());std::iota(parent.begin(),parent.end(),0);std::function<int(int)> find=[&](int x){return parent[x]==x?x:parent[x]=find(parent[x]);};std::vector<std::pair<int,int>> different;for(std::size_t i=0;i<clues.size();++i){auto a=std::lower_bound(labels.begin(),labels.end(),clues[i].first),b=std::lower_bound(labels.begin(),labels.end(),clues[i].second);if(a==labels.end()||*a!=clues[i].first||b==labels.end()||*b!=clues[i].second)return std::nullopt;int x=static_cast<int>(a-labels.begin()),y=static_cast<int>(b-labels.begin());if(clues[i].equal)parent[find(x)]=find(y);else different.push_back({x,y});for(auto edge:different)if(find(edge.first)==find(edge.second))return std::optional<std::size_t>{i+1};}return std::optional<std::size_t>{};""",
        """auto r=minimal_contradiction_prefix({"a","b","c"},{{"a","b",false},{"b","c",true},{"a","c",true}});assert(r&&*r&&**r==3);
    auto none=minimal_contradiction_prefix({"a","b"},{{"a","b",false}});assert(none&&!*none);
    assert(minimal_contradiction_prefix({},{} )&&!*minimal_contradiction_prefix({},{}));
    assert(!minimal_contradiction_prefix({"b","a"},{}));
    assert(!minimal_contradiction_prefix({"a"},{{"a","x",true}}));""",
        ["labels are sorted unique nonempty", "all clue endpoints are known", "prefix length is one-based", "old inequalities are rechecked after merges", "consistent input returns empty inner optional"],
        "incremental disjoint-set equality closure with persistent inequality checks", ["contradiction", "prefix", "union-find"],
    )

    if len(specs) != 51:
        raise ValueError(f"expected 51 independent p3 specifications, got {len(specs)}")
    return specs
