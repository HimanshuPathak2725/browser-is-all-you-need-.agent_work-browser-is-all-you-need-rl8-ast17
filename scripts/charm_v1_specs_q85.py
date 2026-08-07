#!/usr/bin/env python3
"""Independently authored clean-room task specifications for CHARM V1 q85."""

from __future__ import annotations

import re


def build_specs(Spec):
    specs = []

    def add(topic, slug, title, contract, types, signature, body, checks, edges, strategy):
        namespace = re.sub(r"[^a-z0-9]+", "_", topic.casefold()).strip("_")
        ns = f"charm::v1q85_29635::{namespace}"
        definition = f"namespace {ns} {{\n{signature} {{ {body} }}\n}}"
        tests = f"using namespace {ns};\nint main() {{ {checks} return 0; }}"
        specs.append(
            Spec(
                topic,
                slug,
                title,
                contract,
                types,
                signature,
                definition,
                tests,
                tuple(edges.split("|")),
                strategy,
                (slug, namespace, "clean-room-v1q85-29635"),
            )
        )

    # Allergies: temporal rule automata, counterfactual attribution, and
    # bounded set-cover planning have unrelated APIs and solution graphs.
    add(
        "Allergies", "sustained-trigger-alerts", "Sustained trigger alerts",
        "Evaluate named exposure rules over a sequence of bit masks. A rule activates at the first index completing its required consecutive run, where every required bit is present and every forbidden bit is absent. Rule names are unique and nonempty, required and forbidden masks are disjoint, run lengths are positive, and samples may use only known_mask bits. Return activations ordered by index then rule name.",
        "struct TriggerRule { std::string name; std::uint32_t required; std::uint32_t forbidden; std::size_t consecutive; }; struct TriggerAlert { std::string name; std::size_t index; };",
        "std::optional<std::vector<TriggerAlert>> sustained_trigger_alerts(const std::vector<std::uint32_t>& samples, std::uint32_t known_mask, const std::vector<TriggerRule>& rules)",
        "std::set<std::string> names;for(const auto& r:rules)if(r.name.empty()||r.consecutive==0||(r.required&r.forbidden)!=0U||((r.required|r.forbidden)&~known_mask)!=0U||!names.insert(r.name).second)return std::nullopt;for(auto sample:samples)if((sample&~known_mask)!=0U)return std::nullopt;std::vector<std::size_t> streak(rules.size());std::vector<unsigned char> emitted(rules.size());std::vector<TriggerAlert> out;for(std::size_t i=0;i<samples.size();++i)for(std::size_t j=0;j<rules.size();++j){const auto& r=rules[j];const bool hit=(samples[i]&r.required)==r.required&&(samples[i]&r.forbidden)==0U;streak[j]=hit?streak[j]+1U:0U;if(!emitted[j]&&streak[j]>=r.consecutive){out.push_back({r.name,i});emitted[j]=1U;}}std::sort(out.begin(),out.end(),[](const auto& a,const auto& b){return std::tie(a.index,a.name)<std::tie(b.index,b.name);});return out;",
        "auto r=sustained_trigger_alerts({1U,3U,1U,1U},3U,{{\"itch\",1U,2U,2U},{\"both\",3U,0U,1U}});require_case(r&&r->size()==2U&&r->at(0).name==\"both\"&&r->at(0).index==1U&&r->at(1).index==3U);require_case(sustained_trigger_alerts({},7U,{})->empty());require_case(!sustained_trigger_alerts({8U},7U,{}));require_case(!sustained_trigger_alerts({},3U,{{\"x\",1U,1U,1U}}));require_case(!sustained_trigger_alerts({},3U,{{\"x\",1U,0U,0U}}));",
        "activation indices are completion indices|a rule emits at most once|ties use lexical rule names|unknown sample bits reject|invalid rule domains reject atomically",
        "independent per-rule run automata followed by canonical activation ordering",
    )
    add(
        "Allergies", "counterfactual-trigger-credit", "Counterfactual trigger credit",
        "For each episode, sum the weights of its distinct ingredients. Credit an ingredient exactly when the episode reaches threshold and removing that ingredient alone would make it fall below threshold. Ingredient weights are unique, nonempty, and positive; episode ingredient names must be known and nonempty; threshold is positive. Return credited episode counts ordered by descending count then ingredient name, omitting zero counts.",
        "struct IngredientWeight { std::string ingredient; int weight; }; struct TriggerCredit { std::string ingredient; std::size_t episodes; };",
        "std::optional<std::vector<TriggerCredit>> counterfactual_trigger_credit(const std::vector<IngredientWeight>& weights, const std::vector<std::vector<std::string>>& episodes, int threshold)",
        "if(threshold<=0)return std::nullopt;std::map<std::string,int> table;for(const auto& w:weights)if(w.ingredient.empty()||w.weight<=0||!table.emplace(w.ingredient,w.weight).second)return std::nullopt;std::map<std::string,std::size_t> counts;for(const auto& episode:episodes){std::set<std::string> unique;long long total=0;for(const auto& name:episode){auto it=table.find(name);if(name.empty()||it==table.end())return std::nullopt;if(unique.insert(name).second)total+=it->second;}if(total>=threshold)for(const auto& name:unique)if(total-table[name]<threshold)++counts[name];}std::vector<TriggerCredit> out;for(const auto& item:counts)if(item.second!=0U)out.push_back({item.first,item.second});std::sort(out.begin(),out.end(),[](const auto& a,const auto& b){return a.episodes!=b.episodes?a.episodes>b.episodes:a.ingredient<b.ingredient;});return out;",
        "auto r=counterfactual_trigger_credit({{\"a\",3},{\"b\",2},{\"c\",4}},{{\"a\",\"b\"},{\"c\"},{\"a\",\"a\",\"c\"}},5);require_case(r&&r->size()==3U&&r->at(0).ingredient==\"a\"&&r->at(0).episodes==2U&&r->at(2).ingredient==\"c\");require_case(counterfactual_trigger_credit({}, {},1)->empty());require_case(!counterfactual_trigger_credit({}, {},0));require_case(!counterfactual_trigger_credit({{\"a\",1},{\"a\",2}}, {},1));require_case(!counterfactual_trigger_credit({{\"a\",1}},{{\"b\"}},1));",
        "duplicate episode ingredients count once|only threshold-changing ingredients receive credit|zero-credit ingredients are omitted|ties are lexical|unknown ingredients reject the complete request",
        "episode-local counterfactual removal scoring over a validated weight dictionary",
    )
    add(
        "Allergies", "minimum-panel-sensor-cover", "Minimum panel sensor cover",
        "Choose sensor IDs whose bit coverage includes every required allergen bit. At most twenty sensors and twenty known bits are allowed. Sensor IDs are unique and nonempty, coverage uses only known_mask, required_mask is nonzero and within known_mask. Minimize sensor count, then lexicographically compare the sorted ID list. Return no inner value if coverage is impossible.",
        "struct PanelSensor { std::string id; std::uint32_t coverage; };",
        "std::optional<std::optional<std::vector<std::string>>> minimum_panel_sensor_cover(std::uint32_t known_mask, std::uint32_t required_mask, const std::vector<PanelSensor>& sensors)",
        "if(required_mask==0U||(required_mask&~known_mask)!=0U||sensors.size()>20U)return std::nullopt;std::set<std::string> ids;for(const auto& s:sensors)if(s.id.empty()||(s.coverage&~known_mask)!=0U||!ids.insert(s.id).second)return std::nullopt;std::optional<std::vector<std::string>> best;const std::uint64_t limit=std::uint64_t{1}<<sensors.size();for(std::uint64_t mask=0;mask<limit;++mask){std::uint32_t cover=0;std::vector<std::string> chosen;for(std::size_t i=0;i<sensors.size();++i)if((mask&(std::uint64_t{1}<<i))!=0U){cover|=sensors[i].coverage;chosen.push_back(sensors[i].id);}if((cover&required_mask)!=required_mask)continue;std::sort(chosen.begin(),chosen.end());if(!best||chosen.size()<best->size()||(chosen.size()==best->size()&&chosen<*best))best=chosen;}return best;",
        "auto r=minimum_panel_sensor_cover(7U,7U,{{\"z\",3U},{\"a\",5U},{\"b\",2U}});require_case(r&&*r&&**r==std::vector<std::string>({\"a\",\"b\"}));auto impossible=minimum_panel_sensor_cover(3U,3U,{{\"a\",1U}});require_case(impossible&&!*impossible);require_case(!minimum_panel_sensor_cover(3U,0U,{}));require_case(!minimum_panel_sensor_cover(3U,1U,{{\"\",1U}}));require_case(!minimum_panel_sensor_cover(1U,1U,std::vector<PanelSensor>(21,PanelSensor{\"x\",1U})));",
        "required coverage is nonempty|impossible coverage is distinct from invalid input|the primary objective is cardinality|lexical ID order breaks ties|enumeration is explicitly bounded",
        "bounded subset enumeration with coverage pruning and canonical two-level optimization",
    )

    # Bank Account: tranche matching, double-entry reconciliation, and
    # dependency-clearing are separate financial mechanisms.
    add(
        "Bank Account", "fifo-deposit-backing", "FIFO deposit backing",
        "Match nonnegative deposits to chronological nonnegative withdrawals using first-in-first-out tranches. Each event has a strictly increasing sequence number. Return the amount of every withdrawal left unbacked and the remaining deposit tranches. Reject overflow and malformed chronology without a partial result.",
        "enum class CashKind { deposit, withdrawal }; struct CashEvent { std::uint64_t sequence; CashKind kind; long long cents; }; struct BackingResult { std::vector<long long> unbacked; std::vector<long long> remaining_deposits; };",
        "std::optional<BackingResult> fifo_deposit_backing(const std::vector<CashEvent>& events)",
        "std::deque<long long> tranches;std::vector<long long> unbacked;for(std::size_t i=0;i<events.size();++i){const auto& e=events[i];if(e.cents<0||(i>0&&e.sequence<=events[i-1].sequence))return std::nullopt;if(e.kind==CashKind::deposit){if(e.cents!=0)tranches.push_back(e.cents);continue;}long long need=e.cents;while(need>0&&!tranches.empty()){const long long used=std::min(need,tranches.front());need-=used;tranches.front()-=used;if(tranches.front()==0)tranches.pop_front();}unbacked.push_back(need);}return BackingResult{unbacked,std::vector<long long>(tranches.begin(),tranches.end())};",
        "auto r=fifo_deposit_backing({{1,CashKind::deposit,5},{2,CashKind::deposit,4},{3,CashKind::withdrawal,7},{4,CashKind::withdrawal,4}});require_case(r&&r->unbacked==std::vector<long long>({0,2})&&r->remaining_deposits.empty());require_case(fifo_deposit_backing({})->unbacked.empty());require_case(!fifo_deposit_backing({{2,CashKind::deposit,1},{2,CashKind::withdrawal,1}}));require_case(!fifo_deposit_backing({{1,CashKind::deposit,-1}}));require_case(fifo_deposit_backing({{1,CashKind::withdrawal,3}})->unbacked.at(0)==3);",
        "sequence numbers are strictly increasing|zero deposits create no tranche|withdrawals consume oldest funds first|unbacked values retain event order|invalid input has no partial result",
        "deque-based FIFO tranche consumption with per-withdrawal deficit reporting",
    )
    add(
        "Bank Account", "multi-currency-journal-audit", "Multi-currency journal audit",
        "Audit double-entry journals independently per currency. Every posting names a nonempty journal, account, and three-letter uppercase currency and has a nonzero signed amount. For each journal and currency the signed sum must be zero. Return final account balances keyed by account plus currency; return an empty inner value when any journal is unbalanced.",
        "struct JournalPosting { std::string journal; std::string account; std::string currency; long long signed_cents; };",
        "std::optional<std::optional<std::map<std::string,long long>>> audit_multi_currency_journal(const std::vector<JournalPosting>& postings)",
        "std::map<std::pair<std::string,std::string>,long long> journals;std::map<std::string,long long> balances;for(const auto& p:postings){if(p.journal.empty()||p.account.empty()||p.currency.size()!=3U||p.signed_cents==0||!std::all_of(p.currency.begin(),p.currency.end(),[](unsigned char c){return c>='A'&&c<='Z';}))return std::nullopt;auto& js=journals[{p.journal,p.currency}];if((p.signed_cents>0&&js>std::numeric_limits<long long>::max()-p.signed_cents)||(p.signed_cents<0&&js<std::numeric_limits<long long>::min()-p.signed_cents))return std::nullopt;js+=p.signed_cents;const std::string key=p.account+\"@\"+p.currency;auto& balance=balances[key];if((p.signed_cents>0&&balance>std::numeric_limits<long long>::max()-p.signed_cents)||(p.signed_cents<0&&balance<std::numeric_limits<long long>::min()-p.signed_cents))return std::nullopt;balance+=p.signed_cents;}for(const auto& item:journals)if(item.second!=0)return std::optional<std::map<std::string,long long>>{};return balances;",
        "auto r=audit_multi_currency_journal({{\"j1\",\"cash\",\"USD\",100},{\"j1\",\"sales\",\"USD\",-100},{\"j2\",\"cash\",\"EUR\",5},{\"j2\",\"fee\",\"EUR\",-5}});require_case(r&&*r&&(**r).at(\"cash@USD\")==100&&(**r).at(\"fee@EUR\")==-5);auto bad=audit_multi_currency_journal({{\"j\",\"a\",\"USD\",1}});require_case(bad&&!*bad);require_case(audit_multi_currency_journal({})->value().empty());require_case(!audit_multi_currency_journal({{\"\",\"a\",\"USD\",1}}));require_case(!audit_multi_currency_journal({{\"j\",\"a\",\"usd\",1}}));",
        "balancing is per journal and currency|invalid fields reject|unbalanced books are a valid negative result|balances use canonical account-at-currency keys|checked accumulation is mandatory",
        "two-level journal reconciliation with independent checked account aggregation",
    )
    add(
        "Bank Account", "clearing-dependency-order", "Clearing dependency order",
        "Order cheque batches whose dependencies must clear first. Batch IDs are unique and nonempty; every dependency endpoint must be known, distinct, and pair-unique. At each step select the lexicographically smallest currently ready batch. Return an empty inner value if the dependency graph has a cycle.",
        "struct ClearingDependency { std::string prerequisite; std::string batch; };",
        "std::optional<std::optional<std::vector<std::string>>> clearing_dependency_order(const std::vector<std::string>& batches, const std::vector<ClearingDependency>& dependencies)",
        "std::set<std::string> domain(batches.begin(),batches.end());if(domain.size()!=batches.size()||domain.count(\"\")!=0U)return std::nullopt;std::map<std::string,std::set<std::string>> edges;std::map<std::string,std::size_t> indegree;for(const auto& id:batches)indegree[id]=0;std::set<std::pair<std::string,std::string>> seen;for(const auto& d:dependencies){if(d.prerequisite==d.batch||domain.count(d.prerequisite)==0U||domain.count(d.batch)==0U||!seen.emplace(d.prerequisite,d.batch).second)return std::nullopt;edges[d.prerequisite].insert(d.batch);++indegree[d.batch];}std::set<std::string> ready;for(const auto& item:indegree)if(item.second==0U)ready.insert(item.first);std::vector<std::string> out;while(!ready.empty()){const std::string id=*ready.begin();ready.erase(ready.begin());out.push_back(id);for(const auto& next:edges[id])if(--indegree[next]==0U)ready.insert(next);}if(out.size()!=batches.size())return std::optional<std::vector<std::string>>{};return out;",
        "auto r=clearing_dependency_order({\"c\",\"a\",\"b\"},{{\"a\",\"c\"}});require_case(r&&*r&&**r==std::vector<std::string>({\"a\",\"b\",\"c\"}));auto cycle=clearing_dependency_order({\"a\",\"b\"},{{\"a\",\"b\"},{\"b\",\"a\"}});require_case(cycle&&!*cycle);require_case(clearing_dependency_order({},{})->value().empty());require_case(!clearing_dependency_order({\"a\",\"a\"},{}));require_case(!clearing_dependency_order({\"a\"},{{\"a\",\"x\"}}));",
        "ready batches use lexical priority|cycles are a valid negative result|all endpoints are declared|duplicate edges reject|empty input has an empty order",
        "lexically prioritized Kahn traversal with explicit cyclic-result separation",
    )

    # Binary Search Tree: search-cost instrumentation, swapped-key diagnosis,
    # and gap tables use different traversal and validation state.
    add(
        "Binary Search Tree", "validated-search-costs", "Validated search costs",
        "Validate an indexed strict binary search tree rooted at index zero, then report the number of visited nodes for each query, using zero for a miss after traversal. Child indices use -1 for absent, every nonroot has exactly one parent, all nodes are reachable, and keys are unique.",
        "struct SearchNode { int key; int left; int right; };",
        "std::optional<std::vector<std::size_t>> validated_search_costs(const std::vector<SearchNode>& nodes, const std::vector<int>& queries)",
        "if(nodes.empty())return queries.empty()?std::optional<std::vector<std::size_t>>{std::vector<std::size_t>{}}:std::nullopt;std::vector<unsigned char> parents(nodes.size());struct Frame{int index;long long low;long long high;};std::vector<Frame> stack{{0,std::numeric_limits<long long>::min(),std::numeric_limits<long long>::max()}};std::vector<unsigned char> seen(nodes.size());while(!stack.empty()){const auto f=stack.back();stack.pop_back();if(f.index<0||f.index>=static_cast<int>(nodes.size())||seen[static_cast<std::size_t>(f.index)])return std::nullopt;const auto& n=nodes[static_cast<std::size_t>(f.index)];if(n.key<=f.low||n.key>=f.high)return std::nullopt;seen[static_cast<std::size_t>(f.index)]=1U;for(int child:{n.left,n.right})if(child<-1||child>=static_cast<int>(nodes.size())||(child>=0&&++parents[static_cast<std::size_t>(child)]>1U))return std::nullopt;if(n.right>=0)stack.push_back({n.right,n.key,f.high});if(n.left>=0)stack.push_back({n.left,f.low,n.key});}if(parents[0]!=0U||std::find(seen.begin(),seen.end(),0U)!=seen.end())return std::nullopt;std::vector<std::size_t> out;for(int q:queries){int at=0;std::size_t cost=0;bool found=false;while(at>=0){++cost;const auto& n=nodes[static_cast<std::size_t>(at)];if(q==n.key){found=true;break;}at=q<n.key?n.left:n.right;}out.push_back(found?cost:0U);}return out;",
        "auto r=validated_search_costs({{4,1,2},{2,-1,-1},{7,-1,-1}},{4,2,6});require_case(r&&*r==std::vector<std::size_t>({1,2,0}));require_case(validated_search_costs({},{})->empty());require_case(!validated_search_costs({}, {1}));require_case(!validated_search_costs({{2,1,-1},{3,-1,-1}},{}));require_case(!validated_search_costs({{2,-1,-1},{1,-1,-1}},{}));",
        "the root is index zero|strict ordering uses open bounds|every node has one reachable position|found costs count the root|misses are represented by zero",
        "bounded structural DFS followed by instrumented branch-by-branch query search",
    )
    add(
        "Binary Search Tree", "swapped-key-diagnosis", "Swapped key diagnosis",
        "Given an indexed binary tree shape that would become a strict BST after swapping exactly two node keys, return the two node indices in ascending order. The shape must be a reachable single-parent tree rooted at zero. Return an empty inner value if the keys already form a BST or no single swap repairs them.",
        "struct KeyNode { int key; int left; int right; };",
        "std::optional<std::optional<std::pair<std::size_t,std::size_t>>> diagnose_swapped_bst_keys(const std::vector<KeyNode>& nodes)",
        "if(nodes.empty())return std::nullopt;std::vector<unsigned char> parent(nodes.size()),seen(nodes.size());std::vector<std::size_t> inorder;std::function<bool(int)> walk=[&](int at){if(at<0)return true;if(at>=static_cast<int>(nodes.size())||seen[static_cast<std::size_t>(at)])return false;seen[static_cast<std::size_t>(at)]=1U;const auto& n=nodes[static_cast<std::size_t>(at)];for(int child:{n.left,n.right})if(child<-1||child>=static_cast<int>(nodes.size())||(child>=0&&++parent[static_cast<std::size_t>(child)]>1U))return false;if(!walk(n.left))return false;inorder.push_back(static_cast<std::size_t>(at));return walk(n.right);};if(!walk(0)||parent[0]!=0U||std::find(seen.begin(),seen.end(),0U)!=seen.end())return std::nullopt;auto sorted=[&](std::size_t a,std::size_t b){for(std::size_t k=1;k<inorder.size();++k){const int left=inorder[k-1]==a?nodes[b].key:inorder[k-1]==b?nodes[a].key:nodes[inorder[k-1]].key;const int right=inorder[k]==a?nodes[b].key:inorder[k]==b?nodes[a].key:nodes[inorder[k]].key;if(left>=right)return false;}return true;};if(sorted(nodes.size(),nodes.size()))return std::optional<std::pair<std::size_t,std::size_t>>{};for(std::size_t i=0;i<nodes.size();++i)for(std::size_t j=i+1;j<nodes.size();++j)if(sorted(i,j))return std::pair<std::size_t,std::size_t>{i,j};return std::optional<std::pair<std::size_t,std::size_t>>{};",
        "auto r=diagnose_swapped_bst_keys({{2,1,2},{3,-1,-1},{1,-1,-1}});require_case(r&&*r&&**r==std::pair<std::size_t,std::size_t>{1U,2U});auto good=diagnose_swapped_bst_keys({{2,1,2},{1,-1,-1},{3,-1,-1}});require_case(good&&!*good);require_case(!diagnose_swapped_bst_keys({}));require_case(!diagnose_swapped_bst_keys({{1,1,1},{2,-1,-1}}));require_case(!diagnose_swapped_bst_keys({{1,2,-1},{2,-1,-1},{3,-1,-1}}));",
        "tree shape is validated independently of keys|already sorted input is not a repair|the returned indices are ascending|strict duplicates cannot be repaired|the first ascending index pair is canonical",
        "inorder index extraction followed by bounded counterfactual two-key validation",
    )
    add(
        "Binary Search Tree", "neighbor-gap-table", "Neighbor gap table",
        "Validate an indexed strict BST and return one row per node in node-index order containing optional predecessor and successor key gaps. Gaps are positive long long differences. The tree is rooted at zero, every child has one parent, and every node is reachable.",
        "struct GapNode { int key; int left; int right; }; struct NeighborGaps { std::optional<long long> predecessor_gap; std::optional<long long> successor_gap; };",
        "std::optional<std::vector<NeighborGaps>> bst_neighbor_gap_table(const std::vector<GapNode>& nodes)",
        "if(nodes.empty())return std::vector<NeighborGaps>{};std::vector<unsigned char> parents(nodes.size()),seen(nodes.size());std::vector<std::size_t> order;std::function<bool(int,long long,long long)> visit=[&](int at,long long low,long long high){if(at<0)return true;if(at>=static_cast<int>(nodes.size())||seen[static_cast<std::size_t>(at)])return false;const auto& n=nodes[static_cast<std::size_t>(at)];if(n.key<=low||n.key>=high)return false;seen[static_cast<std::size_t>(at)]=1U;for(int child:{n.left,n.right})if(child<-1||child>=static_cast<int>(nodes.size())||(child>=0&&++parents[static_cast<std::size_t>(child)]>1U))return false;if(!visit(n.left,low,n.key))return false;order.push_back(static_cast<std::size_t>(at));return visit(n.right,n.key,high);};if(!visit(0,std::numeric_limits<long long>::min(),std::numeric_limits<long long>::max())||parents[0]!=0U||std::find(seen.begin(),seen.end(),0U)!=seen.end())return std::nullopt;std::vector<NeighborGaps> out(nodes.size());for(std::size_t i=0;i<order.size();++i){const auto index=order[i];if(i>0)out[index].predecessor_gap=static_cast<long long>(nodes[index].key)-nodes[order[i-1]].key;if(i+1<order.size())out[index].successor_gap=static_cast<long long>(nodes[order[i+1]].key)-nodes[index].key;}return out;",
        "auto r=bst_neighbor_gap_table({{10,1,2},{4,-1,-1},{15,-1,-1}});require_case(r&&r->at(0).predecessor_gap==6&&r->at(0).successor_gap==5&&r->at(1).predecessor_gap==std::nullopt&&r->at(2).successor_gap==std::nullopt);require_case(bst_neighbor_gap_table({})->empty());require_case(!bst_neighbor_gap_table({{2,1,-1},{3,-1,-1}}));require_case(!bst_neighbor_gap_table({{2,-1,-1},{1,-1,-1}}));require_case(bst_neighbor_gap_table({{7,-1,-1}})->at(0).predecessor_gap==std::nullopt);",
        "output order is node-index order|neighbor relations come from inorder order|outer nodes have one absent gap|gaps use wide arithmetic|malformed shapes reject",
        "validated recursive inorder traversal with index-addressed adjacent-difference projection",
    )

    # Circular Buffer: feasibility, canonical compaction, and generation-token
    # replay each exercise a distinct cyclic state model.
    add(
        "Circular Buffer", "minimum-feasible-ring-capacity", "Minimum feasible ring capacity",
        "Given signed producer-consumer deltas applied in order, find the smallest positive ring capacity and smallest initial occupancy that keep occupancy within zero through capacity. Positive deltas produce, negative deltas consume. Return no inner result if max_capacity cannot support the trace; max_capacity is positive.",
        "struct RingSizing { long long capacity; long long initial_occupancy; };",
        "std::optional<std::optional<RingSizing>> minimum_feasible_ring_capacity(const std::vector<long long>& deltas, long long max_capacity)",
        "if(max_capacity<=0)return std::nullopt;long long prefix=0,min_prefix=0,max_prefix=0;for(long long delta:deltas){if((delta>0&&prefix>std::numeric_limits<long long>::max()-delta)||(delta<0&&prefix<std::numeric_limits<long long>::min()-delta))return std::nullopt;prefix+=delta;min_prefix=std::min(min_prefix,prefix);max_prefix=std::max(max_prefix,prefix);}if(max_prefix-min_prefix>max_capacity)return std::optional<RingSizing>{};const long long initial=-min_prefix;const long long capacity=std::max<long long>(1,max_prefix-min_prefix);return RingSizing{capacity,initial};",
        "auto r=minimum_feasible_ring_capacity({-2,5,-1},10);require_case(r&&*r&&(**r).capacity==5&&(**r).initial_occupancy==2);auto empty=minimum_feasible_ring_capacity({},3);require_case(empty&&*empty&&(**empty).capacity==1&&(**empty).initial_occupancy==0);auto no=minimum_feasible_ring_capacity({5},4);require_case(no&&!*no);require_case(!minimum_feasible_ring_capacity({},0));require_case(minimum_feasible_ring_capacity({-3},3)->value().initial_occupancy==3);",
        "capacity is strictly positive|initial occupancy is minimized after capacity|all prefixes must be feasible|capacity excess is a valid negative result|overflow rejects",
        "prefix-extrema feasibility derivation with canonical minimal initial state",
    )
    add(
        "Circular Buffer", "clockwise-ring-compaction", "Clockwise ring compaction",
        "Compact distinct positive item IDs in a cyclic slot array into one contiguous clockwise block while preserving their cyclic encounter order. Empty slots are zero. Evaluate every possible block start; minimize total clockwise movement, then the start index. Return the chosen start, movement cost, and final slots. Moving an item may wrap but may not move counterclockwise.",
        "struct RingCompaction { std::size_t start; std::uint64_t clockwise_moves; std::vector<int> slots; };",
        "std::optional<RingCompaction> clockwise_ring_compaction(const std::vector<int>& slots)",
        "if(slots.empty())return std::nullopt;std::set<int> ids;std::vector<std::pair<std::size_t,int>> items;for(std::size_t i=0;i<slots.size();++i)if(slots[i]!=0){if(slots[i]<0||!ids.insert(slots[i]).second)return std::nullopt;items.push_back({i,slots[i]});}if(items.empty())return RingCompaction{0,0,slots};std::optional<RingCompaction> best;for(std::size_t start=0;start<slots.size();++start){std::uint64_t cost=0;std::vector<int> result(slots.size());bool valid=true;for(std::size_t k=0;k<items.size();++k){const std::size_t target=(start+k)%slots.size();const std::size_t move=(target+slots.size()-items[k].first)%slots.size();if(move>=slots.size()){valid=false;break;}cost+=move;result[target]=items[k].second;}if(valid&&(!best||cost<best->clockwise_moves||(cost==best->clockwise_moves&&start<best->start)))best=RingCompaction{start,cost,result};}return best;",
        "auto r=clockwise_ring_compaction({1,0,2,0});require_case(r&&r->clockwise_moves==1U&&r->start==0U&&r->slots==std::vector<int>({1,2,0,0}));auto e=clockwise_ring_compaction({0,0});require_case(e&&e->start==0U&&e->clockwise_moves==0U);require_case(!clockwise_ring_compaction({}));require_case(!clockwise_ring_compaction({1,-1}));require_case(!clockwise_ring_compaction({1,0,1}));",
        "item IDs are distinct positive values|relative encounter order is preserved|movement is clockwise modulo capacity|cost ties choose the smallest start|an all-empty ring is already compact",
        "all-origin cyclic placement evaluation with stable item order and lexicographic objective",
    )
    add(
        "Circular Buffer", "generation-token-replay", "Generation token replay",
        "Replay writes and reads on fixed ring slots carrying monotonically increasing generation numbers. A write replaces a slot value and increments its generation; a read token succeeds only when slot and generation match the current state. Return read values as optionals in command order and final generations. Capacity is positive, slots are in range, and generation overflow rejects the complete replay.",
        "enum class RingOpKind { write, read }; struct RingOp { RingOpKind kind; std::size_t slot; std::uint64_t generation; int value; }; struct GenerationReplay { std::vector<std::optional<int>> reads; std::vector<std::uint64_t> generations; };",
        "std::optional<GenerationReplay> replay_generation_tokens(std::size_t capacity, const std::vector<RingOp>& operations)",
        "if(capacity==0)return std::nullopt;std::vector<std::uint64_t> generations(capacity);std::vector<std::optional<int>> values(capacity);std::vector<std::optional<int>> reads;for(const auto& op:operations){if(op.slot>=capacity)return std::nullopt;if(op.kind==RingOpKind::write){if(generations[op.slot]==std::numeric_limits<std::uint64_t>::max())return std::nullopt;++generations[op.slot];values[op.slot]=op.value;}else{if(op.generation==generations[op.slot]&&values[op.slot])reads.push_back(values[op.slot]);else reads.push_back(std::nullopt);}}return GenerationReplay{reads,generations};",
        "auto r=replay_generation_tokens(2,{{RingOpKind::write,0,0,7},{RingOpKind::read,0,1,0},{RingOpKind::write,0,0,9},{RingOpKind::read,0,1,0},{RingOpKind::read,0,2,0}});require_case(r&&r->reads==std::vector<std::optional<int>>({7,std::nullopt,9})&&r->generations==std::vector<std::uint64_t>({2,0}));require_case(replay_generation_tokens(1,{})->reads.empty());require_case(!replay_generation_tokens(0,{}));require_case(!replay_generation_tokens(1,{{RingOpKind::read,1,0,0}}));require_case(!replay_generation_tokens(1,{{static_cast<RingOpKind>(9),0,0,0}}));",
        "writes increment before exposing a token|stale reads return empty without mutation|unwritten generation zero is not readable|slot bounds are strict|read results retain operation order",
        "slot-local generation state replay with explicit stale-token classification",
    )

    # Clock: network timing, congruence coincidence, and rational tick
    # scheduling do not recreate the historical clock API.
    add(
        "Clock", "ntp-offset-delay-fractions", "NTP offset and delay fractions",
        "Compute exact NTP-style clock offset and round-trip delay from four signed microsecond timestamps t1 through t4. Require t1<=t4, t2<=t3, and nonnegative delay=(t4-t1)-(t3-t2). Return offset numerator over denominator two in reduced form plus delay. Checked arithmetic is mandatory.",
        "struct TimingFraction { long long numerator; long long denominator; }; struct NtpEstimate { TimingFraction offset; long long delay; };",
        "std::optional<NtpEstimate> ntp_offset_delay(long long t1, long long t2, long long t3, long long t4)",
        "if(t1>t4||t2>t3)return std::nullopt;const long double raw_delay=(static_cast<long double>(t4)-t1)-(static_cast<long double>(t3)-t2);const long double raw_num=(static_cast<long double>(t2)-t1)+(static_cast<long double>(t3)-t4);if(raw_delay<0||raw_delay>std::numeric_limits<long long>::max()||raw_num<std::numeric_limits<long long>::min()||raw_num>std::numeric_limits<long long>::max())return std::nullopt;long long delay=static_cast<long long>(raw_delay),num=static_cast<long long>(raw_num),den=2;if(num%2==0){num/=2;den=1;}return NtpEstimate{{num,den},delay};",
        "auto r=ntp_offset_delay(0,4,6,10);require_case(r&&r->offset.numerator==0&&r->offset.denominator==1&&r->delay==8);auto half=ntp_offset_delay(0,1,2,4);require_case(half&&half->offset.numerator==-1&&half->offset.denominator==2&&half->delay==3);require_case(!ntp_offset_delay(5,0,1,4));require_case(!ntp_offset_delay(0,4,3,5));require_case(ntp_offset_delay(-5,-4,-3,-2)->delay==2);",
        "offset uses the four-timestamp formula|halves are reduced|delay must be nonnegative|signed timestamps are supported|chronology is validated on both lanes",
        "wide checked four-timestamp arithmetic with exact half-unit normalization",
    )
    add(
        "Clock", "chime-congruence-window", "Chime congruence window",
        "Find every minute in the half-open window [begin,end) at which two repeating chimes ring. Chime A rings when minute is congruent to phase_a modulo period_a and likewise for B. Periods are positive, phases are canonical nonnegative residues, begin and end are nonnegative with begin<=end, and the window length is at most one million.",
        "",
        "std::optional<std::vector<long long>> chime_congruence_window(long long period_a, long long phase_a, long long period_b, long long phase_b, long long begin, long long end)",
        "if(period_a<=0||period_b<=0||phase_a<0||phase_a>=period_a||phase_b<0||phase_b>=period_b||begin<0||begin>end||end-begin>1000000)return std::nullopt;std::vector<long long> out;for(long long minute=begin;minute<end;++minute)if(minute%period_a==phase_a&&minute%period_b==phase_b)out.push_back(minute);return out;",
        "auto r=chime_congruence_window(4,1,6,3,0,30);require_case(r&&*r==std::vector<long long>({9,21}));require_case(chime_congruence_window(2,0,4,1,0,10)->empty());require_case(chime_congruence_window(5,0,5,0,0,1)->at(0)==0);require_case(!chime_congruence_window(0,0,1,0,0,1));require_case(!chime_congruence_window(3,3,2,0,0,5));",
        "the window is half open|phases are canonical residues|incompatible congruences yield an empty vector|minute zero is valid|enumeration has an explicit bound",
        "bounded simultaneous-congruence scan with canonical phase validation",
    )
    add(
        "Clock", "rational-tick-error-diffusion", "Rational tick error diffusion",
        "Schedule count positive tick intervals approximating numerator/denominator microseconds using deterministic error diffusion. numerator is nonnegative, denominator and count are positive, count is at most one million, and every emitted interval is floor or ceil of the rational period. Prefix sums must equal floor(k*numerator/denominator) for each prefix k.",
        "",
        "std::optional<std::vector<long long>> rational_tick_intervals(long long numerator, long long denominator, std::size_t count)",
        "if(numerator<0||denominator<=0||count==0||count>1000000U)return std::nullopt;std::vector<long long> out;out.reserve(count);long long previous=0;for(std::size_t k=1;k<=count;++k){const long double exact=static_cast<long double>(k)*numerator/denominator;if(exact>std::numeric_limits<long long>::max())return std::nullopt;const long long current=static_cast<long long>(std::floor(exact));out.push_back(current-previous);previous=current;}return out;",
        "auto r=rational_tick_intervals(10,3,6);require_case(r&&*r==std::vector<long long>({3,3,4,3,3,4}));auto z=rational_tick_intervals(0,7,3);require_case(z&&*z==std::vector<long long>({0,0,0}));require_case(!rational_tick_intervals(1,0,2));require_case(!rational_tick_intervals(-1,2,2));require_case(!rational_tick_intervals(1,2,0));",
        "prefix totals follow floor of the exact schedule|individual intervals differ by at most one|zero periods are valid|count is positive and bounded|overflow rejects",
        "prefix-floor error diffusion over an exact rational period",
    )

    # Complex Numbers: continued fractions, Hermitian energy, and bounded
    # orbit classification use unrelated numerical kernels.
    add(
        "Complex Numbers", "gaussian-continued-convergent", "Gaussian continued convergent",
        "Evaluate a finite Gaussian-integer continued fraction a0+1/(a1+1/(...)). Coefficients are pairs of signed long long values, the list is nonempty and at most 64 entries, and every reciprocal denominator must have magnitude above epsilon. epsilon is finite and strictly positive; all intermediate components must remain finite.",
        "struct GaussianInteger { long long real; long long imag; };",
        "std::optional<std::complex<double>> gaussian_continued_convergent(const std::vector<GaussianInteger>& coefficients, double epsilon)",
        "if(coefficients.empty()||coefficients.size()>64U||!std::isfinite(epsilon)||epsilon<=0.0)return std::nullopt;std::complex<double> value(static_cast<double>(coefficients.back().real),static_cast<double>(coefficients.back().imag));for(std::size_t i=coefficients.size()-1;i-->0;){if(std::abs(value)<=epsilon)return std::nullopt;value=std::complex<double>(static_cast<double>(coefficients[i].real),static_cast<double>(coefficients[i].imag))+1.0/value;if(!std::isfinite(value.real())||!std::isfinite(value.imag()))return std::nullopt;}return value;",
        "auto r=gaussian_continued_convergent({{1,0},{2,0}},1e-12);require_case(r&&std::abs(r->real()-1.5)<1e-12&&std::abs(r->imag())<1e-12);require_case(gaussian_continued_convergent({{0,1}},1e-9)==std::complex<double>(0,1));require_case(!gaussian_continued_convergent({},1e-9));require_case(!gaussian_continued_convergent({{1,0},{0,0}},1e-9));require_case(!gaussian_continued_convergent({{1,0}},0.0));",
        "evaluation proceeds from the final coefficient|near-zero reciprocal denominators reject|complex coefficients are Gaussian integers|intermediate finiteness is required|length is bounded",
        "reverse finite continued-fraction fold with guarded complex reciprocals",
    )
    add(
        "Complex Numbers", "hermitian-form-energy", "Hermitian form energy",
        "Evaluate the real energy conjugate(z)^T H z for a 2x2 Hermitian matrix H. The diagonal entries are real, the lower off-diagonal is the conjugate of upper by construction, every component is finite, and the final imaginary residual must be at most tolerance. tolerance is finite and nonnegative.",
        "struct Hermitian2 { double h00; std::complex<double> h01; double h11; };",
        "std::optional<double> hermitian_form_energy(const Hermitian2& matrix, const std::array<std::complex<double>,2>& z, double tolerance)",
        "auto finite=[](const std::complex<double>& v){return std::isfinite(v.real())&&std::isfinite(v.imag());};if(!std::isfinite(matrix.h00)||!std::isfinite(matrix.h11)||!finite(matrix.h01)||!finite(z[0])||!finite(z[1])||!std::isfinite(tolerance)||tolerance<0.0)return std::nullopt;const std::complex<double> first=matrix.h00*z[0]+matrix.h01*z[1];const std::complex<double> second=std::conj(matrix.h01)*z[0]+matrix.h11*z[1];const std::complex<double> energy=std::conj(z[0])*first+std::conj(z[1])*second;if(!finite(energy)||std::abs(energy.imag())>tolerance)return std::nullopt;return energy.real();",
        "Hermitian2 h{2.0,{1.0,0.0},3.0};auto r=hermitian_form_energy(h,{{{1.0,0.0},{2.0,0.0}}},1e-12);require_case(r&&std::abs(*r-18.0)<1e-12);auto c=hermitian_form_energy({1.0,{0.0,1.0},1.0},{{{1.0,0.0},{0.0,1.0}}},1e-12);require_case(c&&std::abs(*c)<1e-12);require_case(!hermitian_form_energy(h,{{{1.0,0.0},{2.0,0.0}}},-1.0));require_case(!hermitian_form_energy({std::numeric_limits<double>::infinity(),{},1.0},{{{}, {}}},1.0));require_case(hermitian_form_energy({0.0,{},0.0},{{{}, {}}},0.0)==0.0);",
        "the lower coefficient is the conjugate of h01|conjugation applies to the vector on the left|imaginary residue is tolerance-bounded|all numeric inputs are finite|zero vectors have zero energy",
        "explicit Hermitian matrix-vector product followed by conjugate inner product",
    )
    add(
        "Complex Numbers", "mandelbrot-orbit-classification", "Mandelbrot orbit classification",
        "Iterate z_{n+1}=z_n^2+c from z0=0. Return the first one-based iteration whose squared magnitude exceeds escape_radius squared, or zero when no escape occurs by max_iterations. c and escape_radius must be finite, escape_radius greater than one, and max_iterations in 1..100000.",
        "",
        "std::optional<std::size_t> mandelbrot_escape_iteration(std::complex<double> c, double escape_radius, std::size_t max_iterations)",
        "if(!std::isfinite(c.real())||!std::isfinite(c.imag())||!std::isfinite(escape_radius)||escape_radius<=1.0||max_iterations==0||max_iterations>100000U)return std::nullopt;std::complex<double> z;const double limit=escape_radius*escape_radius;for(std::size_t iteration=1;iteration<=max_iterations;++iteration){z=z*z+c;const double magnitude=std::norm(z);if(!std::isfinite(magnitude)||magnitude>limit)return iteration;}return 0U;",
        "require_case(mandelbrot_escape_iteration({2.0,0.0},2.0,10)==2U);require_case(mandelbrot_escape_iteration({0.0,0.0},2.0,20)==0U);require_case(mandelbrot_escape_iteration({-1.0,0.0},2.0,20)==0U);require_case(!mandelbrot_escape_iteration({},1.0,10));require_case(!mandelbrot_escape_iteration({},2.0,0));",
        "escape comparison is strict|iteration numbers are one based|zero means bounded within the supplied horizon|numeric inputs must be finite|iteration work is explicitly bounded",
        "bounded quadratic-orbit iteration with first-escape classification",
    )

    # Crypto Square: Feistel permutation, keyed Bacon symbols, and Hill blocks
    # share no route-transposition or rectangular-normalization contract.
    add(
        "Crypto Square", "four-round-feistel-blocks", "Four-round Feistel blocks",
        "Encrypt 64-bit blocks represented as left and right uint32 halves using exactly four Feistel rounds. Round i maps (L,R) to (R,L xor rotate_left(R+key_i,i+3)). Decryption applies the exact inverse rounds. Mode is explicit, exactly four keys are required, and addition wraps as uint32_t.",
        "enum class FeistelMode { encrypt, decrypt }; struct WordBlock { std::uint32_t left; std::uint32_t right; };",
        "std::optional<std::vector<WordBlock>> four_round_feistel(const std::vector<WordBlock>& blocks, const std::vector<std::uint32_t>& keys, FeistelMode mode)",
        "if(keys.size()!=4U||(mode!=FeistelMode::encrypt&&mode!=FeistelMode::decrypt))return std::nullopt;auto rotate=[](std::uint32_t value,unsigned amount){amount%=32U;return static_cast<std::uint32_t>((value<<amount)|(value>>(32U-amount)));};std::vector<WordBlock> out=blocks;for(auto& block:out){std::uint32_t left=block.left,right=block.right;if(mode==FeistelMode::encrypt){for(std::size_t i=0;i<4U;++i){const std::uint32_t next=left^rotate(static_cast<std::uint32_t>(right+keys[i]),static_cast<unsigned>(i+3U));left=right;right=next;}}else{for(std::size_t step=4U;step-->0;){const std::uint32_t old_right=left;const std::uint32_t old_left=right^rotate(static_cast<std::uint32_t>(old_right+keys[step]),static_cast<unsigned>(step+3U));left=old_left;right=old_right;}}block={left,right};}return out;",
        "std::vector<WordBlock> plain{{1U,2U},{0U,0U}};std::vector<std::uint32_t> keys{3U,5U,7U,11U};auto encrypted=four_round_feistel(plain,keys,FeistelMode::encrypt);require_case(encrypted&&*encrypted!=plain);auto decrypted=four_round_feistel(*encrypted,keys,FeistelMode::decrypt);require_case(decrypted&&*decrypted==plain);require_case(four_round_feistel({},keys,FeistelMode::encrypt)->empty());require_case(!four_round_feistel(plain,{1U},FeistelMode::encrypt));require_case(!four_round_feistel(plain,keys,static_cast<FeistelMode>(9)));",
        "exactly four rounds are used|uint32 addition deliberately wraps|decryption reverses both swap and round order|empty block vectors are valid|invalid modes reject",
        "explicit reversible four-round Feistel state permutation over fixed-width halves",
    )
    add(
        "Crypto Square", "keyed-bacon-symbol-stream", "Keyed Bacon symbol stream",
        "Encode ASCII letters into five-symbol Bacon groups after constructing a keyed alphabet. The key contributes each first-seen ASCII letter, then remaining a-z; plaintext ignores spaces and hyphens but rejects other bytes. A and B output symbols must differ. Return groups joined by one slash and lowercase/uppercase input is equivalent.",
        "",
        "std::optional<std::string> keyed_bacon_stream(std::string_view plaintext, std::string_view key, char zero_symbol, char one_symbol)",
        "if(zero_symbol==one_symbol)return std::nullopt;auto letter=[](unsigned char c)->char{if(c>='A'&&c<='Z')return static_cast<char>(c-'A'+'a');if(c>='a'&&c<='z')return static_cast<char>(c);return 0;};std::string alphabet;std::set<char> seen;for(unsigned char c:key){const char x=letter(c);if(x==0)return std::nullopt;if(seen.insert(x).second)alphabet.push_back(x);}for(char c='a';c<='z';++c)if(seen.insert(c).second)alphabet.push_back(c);std::map<char,std::size_t> rank;for(std::size_t i=0;i<alphabet.size();++i)rank[alphabet[i]]=i;std::string out;bool first=true;for(unsigned char c:plaintext){if(c==' '||c=='-')continue;const char x=letter(c);if(x==0)return std::nullopt;if(!first)out.push_back('/');first=false;const std::size_t value=rank[x];for(int bit=4;bit>=0;--bit)out.push_back((value&(std::size_t{1}<<bit))?one_symbol:zero_symbol);}return out;",
        "require_case(keyed_bacon_stream(\"Ab\",\"b\",'x','o')==\"xxxxo/xxxxx\");require_case(keyed_bacon_stream(\"A-B a\",\"\",'0','1')->find('/')!=std::string::npos);require_case(keyed_bacon_stream(\"\",\"key\",'a','b')==\"\");require_case(!keyed_bacon_stream(\"a!\",\"\",'0','1'));require_case(!keyed_bacon_stream(\"a\",\"k1\",'0','1'));",
        "the key is deduplicated by first appearance|unkeyed letters follow lexical order|only spaces and hyphens are ignored|groups have exactly five symbols|empty plaintext yields an empty stream",
        "first-occurrence keyed alphabet construction followed by fixed-width binary rank emission",
    )
    add(
        "Crypto Square", "invertible-hill-pairs", "Invertible Hill pairs",
        "Transform lowercase ASCII letter pairs with a 2x2 matrix modulo 26. Encryption multiplies by the supplied matrix; decryption uses its modular inverse. Text length is even, all bytes are a-z, and the determinant must be coprime to 26. Preserve lowercase output and reject unsupported modes.",
        "enum class HillMode { encrypt, decrypt };",
        "std::optional<std::string> hill_pair_transform(std::string_view text, const std::array<int,4>& matrix, HillMode mode)",
        "if(text.size()%2U!=0U||(mode!=HillMode::encrypt&&mode!=HillMode::decrypt))return std::nullopt;for(unsigned char c:text)if(c<'a'||c>'z')return std::nullopt;auto norm=[](long long x){x%=26;if(x<0)x+=26;return static_cast<int>(x);};const int det=norm(static_cast<long long>(matrix[0])*matrix[3]-static_cast<long long>(matrix[1])*matrix[2]);int inverse=-1;for(int x=1;x<26;++x)if((det*x)%26==1){inverse=x;break;}if(inverse<0)return std::nullopt;std::array<int,4> m=matrix;for(auto& x:m)x=norm(x);if(mode==HillMode::decrypt)m={norm(static_cast<long long>(inverse)*m[3]),norm(-static_cast<long long>(inverse)*m[1]),norm(-static_cast<long long>(inverse)*m[2]),norm(static_cast<long long>(inverse)*m[0])};std::string out(text.size(),'a');for(std::size_t i=0;i<text.size();i+=2){const int a=text[i]-'a',b=text[i+1]-'a';out[i]=static_cast<char>('a'+norm(static_cast<long long>(m[0])*a+static_cast<long long>(m[1])*b));out[i+1]=static_cast<char>('a'+norm(static_cast<long long>(m[2])*a+static_cast<long long>(m[3])*b));}return out;",
        "std::array<int,4> m{3,3,2,5};auto encoded=hill_pair_transform(\"help\",m,HillMode::encrypt);require_case(encoded&&*encoded!=\"help\");require_case(hill_pair_transform(*encoded,m,HillMode::decrypt)==\"help\");require_case(hill_pair_transform(\"\",m,HillMode::encrypt)==\"\");require_case(!hill_pair_transform(\"abc\",m,HillMode::encrypt));require_case(!hill_pair_transform(\"AB\",m,HillMode::encrypt));",
        "pairs are independent|negative matrix entries normalize modulo 26|decryption requires a true modular inverse|only lowercase letters are accepted|empty even text is valid",
        "modular determinant inversion and pairwise matrix-vector transformation",
    )

    # Diamond: erosion, constrained routing, and bounded union counting are
    # different grid problems and avoid perimeter-generation APIs.
    add(
        "Diamond", "diamond-erosion-centers", "Diamond erosion centers",
        "Return grid cells that can serve as centers of a filled Manhattan diamond of radius r consisting only of true cells. The grid must be nonempty rectangular, radius is nonnegative, and total cells are at most one million. Output centers in row-major order.",
        "",
        "std::optional<std::vector<std::pair<std::size_t,std::size_t>>> diamond_erosion_centers(const std::vector<std::vector<bool>>& grid, std::size_t radius)",
        "if(grid.empty()||grid[0].empty()||grid.size()>1000000U/grid[0].size())return std::nullopt;const std::size_t rows=grid.size(),columns=grid[0].size();for(const auto& row:grid)if(row.size()!=columns)return std::nullopt;std::vector<std::pair<std::size_t,std::size_t>> out;for(std::size_t r=0;r<rows;++r)for(std::size_t c=0;c<columns;++c){bool ok=true;for(long long dr=-static_cast<long long>(radius);dr<=static_cast<long long>(radius)&&ok;++dr){const long long rr=static_cast<long long>(r)+dr;const long long span=static_cast<long long>(radius)-std::llabs(dr);for(long long dc=-span;dc<=span;++dc){const long long cc=static_cast<long long>(c)+dc;if(rr<0||cc<0||rr>=static_cast<long long>(rows)||cc>=static_cast<long long>(columns)||!grid[static_cast<std::size_t>(rr)][static_cast<std::size_t>(cc)]){ok=false;break;}}}if(ok)out.emplace_back(r,c);}return out;",
        "auto r=diamond_erosion_centers({{true,true,true},{true,true,true},{true,true,true}},1);require_case(r&&*r==std::vector<std::pair<std::size_t,std::size_t>>({{1U,1U}}));auto zero=diamond_erosion_centers({{true,false}},0);require_case(zero&&*zero==std::vector<std::pair<std::size_t,std::size_t>>({{0U,0U}}));require_case(!diamond_erosion_centers({},1));require_case(!diamond_erosion_centers({{}},1));require_case(!diamond_erosion_centers({{true},{true,false}},1));",
        "diamonds include their boundary|centers are row-major|radius zero selects true cells|out-of-grid diamond cells invalidate a center|ragged grids reject",
        "center-by-center Manhattan stencil erosion with explicit boundary rejection",
    )
    add(
        "Diamond", "blocked-diamond-shortest-path", "Blocked diamond shortest path",
        "Find the lexicographically smallest shortest four-neighbor path between two lattice points constrained to the closed Manhattan diamond |x|+|y|<=radius and avoiding blocked cells. Radius is 0..200; endpoints and blocked cells must lie inside; moves are explored in coordinate order. Return an empty inner path when unreachable.",
        "struct LatticePoint { int x; int y; bool operator<(const LatticePoint& other) const { return std::tie(x,y)<std::tie(other.x,other.y); } bool operator==(const LatticePoint& other) const { return x==other.x&&y==other.y; } };",
        "std::optional<std::optional<std::vector<LatticePoint>>> shortest_path_inside_diamond(int radius, LatticePoint start, LatticePoint goal, const std::vector<LatticePoint>& blocked)",
        "auto inside=[&](LatticePoint p){return std::llabs(static_cast<long long>(p.x))+std::llabs(static_cast<long long>(p.y))<=radius;};if(radius<0||radius>200||!inside(start)||!inside(goal))return std::nullopt;std::set<LatticePoint> walls;for(auto p:blocked)if(!inside(p)||!walls.insert(p).second)return std::nullopt;if(walls.count(start)||walls.count(goal))return std::optional<std::vector<LatticePoint>>{};std::queue<LatticePoint> queue;std::map<LatticePoint,LatticePoint> parent;std::set<LatticePoint> seen{start};queue.push(start);const std::array<LatticePoint,4> delta{{{-1,0},{0,-1},{0,1},{1,0}}};while(!queue.empty()){const auto current=queue.front();queue.pop();if(current==goal)break;for(auto d:delta){LatticePoint next{current.x+d.x,current.y+d.y};if(inside(next)&&!walls.count(next)&&seen.insert(next).second){parent[next]=current;queue.push(next);}}}if(!seen.count(goal))return std::optional<std::vector<LatticePoint>>{};std::vector<LatticePoint> path;for(LatticePoint at=goal;;at=parent[at]){path.push_back(at);if(at==start)break;}std::reverse(path.begin(),path.end());return path;",
        "auto r=shortest_path_inside_diamond(2,{0,0},{1,1},{});require_case(r&&*r&&(**r).front()==LatticePoint{0,0}&&(**r).back()==LatticePoint{1,1}&&(**r).size()==3U);auto no=shortest_path_inside_diamond(1,{-1,0},{1,0},{{0,0}});require_case(no&&!*no);require_case(!shortest_path_inside_diamond(-1,{0,0},{0,0},{}));require_case(!shortest_path_inside_diamond(1,{2,0},{0,0},{}));require_case(!shortest_path_inside_diamond(1,{0,0},{0,0},{{1,0},{1,0}}));",
        "paths include both endpoints|the diamond boundary is traversable|blocked endpoints are unreachable not invalid|duplicate blocked cells reject|neighbor order determines canonical shortest paths",
        "coordinate-ordered breadth-first search over a bounded Manhattan domain",
    )
    add(
        "Diamond", "bounded-diamond-union-cells", "Bounded diamond union cells",
        "Count integer lattice cells covered by at least one closed Manhattan diamond. Each radius is nonnegative, at most twelve diamonds are allowed, and the combined bounding box must contain at most one million lattice cells. Duplicate diamonds are valid and union cells count once.",
        "struct LatticeDiamond { int center_x; int center_y; int radius; };",
        "std::optional<std::size_t> bounded_diamond_union_cells(const std::vector<LatticeDiamond>& diamonds)",
        "if(diamonds.size()>12U)return std::nullopt;if(diamonds.empty())return 0U;long long min_x=std::numeric_limits<long long>::max(),max_x=std::numeric_limits<long long>::min(),min_y=min_x,max_y=max_x;for(const auto& d:diamonds){if(d.radius<0)return std::nullopt;min_x=std::min(min_x,static_cast<long long>(d.center_x)-d.radius);max_x=std::max(max_x,static_cast<long long>(d.center_x)+d.radius);min_y=std::min(min_y,static_cast<long long>(d.center_y)-d.radius);max_y=std::max(max_y,static_cast<long long>(d.center_y)+d.radius);}const long long width=max_x-min_x+1,height=max_y-min_y+1;if(width<=0||height<=0||width>1000000/height)return std::nullopt;std::size_t count=0;for(long long y=min_y;y<=max_y;++y)for(long long x=min_x;x<=max_x;++x)if(std::any_of(diamonds.begin(),diamonds.end(),[&](const auto& d){return std::llabs(x-d.center_x)+std::llabs(y-d.center_y)<=d.radius;}))++count;return count;",
        "require_case(bounded_diamond_union_cells({{0,0,1}})==5U);require_case(bounded_diamond_union_cells({{0,0,0},{0,0,0}})==1U);require_case(bounded_diamond_union_cells({})==0U);require_case(!bounded_diamond_union_cells({{0,0,-1}}));require_case(bounded_diamond_union_cells({{0,0,1},{2,0,1}})==9U);",
        "boundaries are included|duplicates do not double count|negative radii reject|empty input covers zero cells|the enumeration box is explicitly bounded",
        "bounded union-box lattice enumeration with short-circuit Manhattan membership",
    )

    # Grade School: repeat normalization, semester planning, and interval-room
    # coloring are independent academic state models.
    add(
        "Grade School", "repeat-course-normalization", "Repeat course normalization",
        "Normalize transcript attempts by course. Attempts have nonempty course IDs, strictly increasing positive terms per course, and scores 0..100. Keep the highest passing score (at least pass_score), breaking ties by latest term; if no attempt passes, keep the latest attempt. Return chosen attempts ordered by course. pass_score is 1..100.",
        "struct CourseAttempt { std::string course; int term; int score; };",
        "std::optional<std::vector<CourseAttempt>> normalize_repeat_courses(const std::vector<CourseAttempt>& attempts, int pass_score)",
        "if(pass_score<1||pass_score>100)return std::nullopt;std::map<std::string,std::vector<CourseAttempt>> grouped;for(const auto& a:attempts)if(a.course.empty()||a.term<=0||a.score<0||a.score>100)return std::nullopt;else grouped[a.course].push_back(a);std::vector<CourseAttempt> out;for(auto& item:grouped){auto& rows=item.second;std::sort(rows.begin(),rows.end(),[](const auto& a,const auto& b){return a.term<b.term;});for(std::size_t i=1;i<rows.size();++i)if(rows[i-1].term==rows[i].term)return std::nullopt;CourseAttempt chosen=rows.back();bool passed=false;for(const auto& row:rows)if(row.score>=pass_score&&(!passed||row.score>chosen.score||(row.score==chosen.score&&row.term>chosen.term))){chosen=row;passed=true;}out.push_back(chosen);}return out;",
        "auto r=normalize_repeat_courses({{\"math\",1,60},{\"math\",2,80},{\"math\",3,80},{\"art\",1,40}},50);require_case(r&&r->size()==2U&&r->at(0).course==\"art\"&&r->at(1).term==3);require_case(normalize_repeat_courses({},50)->empty());require_case(!normalize_repeat_courses({},0));require_case(!normalize_repeat_courses({{\"x\",1,50},{\"x\",1,60}},50));require_case(normalize_repeat_courses({{\"x\",1,20},{\"x\",2,10}},50)->at(0).term==2);",
        "course output is lexical|passing scores dominate failing scores|equal passing scores prefer the latest term|all-failing courses retain the latest attempt|duplicate terms within a course reject",
        "per-course chronological validation with pass-aware best-attempt selection",
    )
    add(
        "Grade School", "prerequisite-semester-plan", "Prerequisite semester plan",
        "Assign courses to the earliest possible one-based semester subject to prerequisite edges. Course IDs are distinct and nonempty; edge endpoints are known, distinct, and unique. At most max_per_semester courses may be assigned, choosing lexical IDs when more are ready. Return an empty inner plan for a cycle.",
        "struct Prerequisite { std::string course; std::string prerequisite; };",
        "std::optional<std::optional<std::vector<std::vector<std::string>>>> prerequisite_semester_plan(const std::vector<std::string>& courses, const std::vector<Prerequisite>& prerequisites, std::size_t max_per_semester)",
        "if(max_per_semester==0)return std::nullopt;std::set<std::string> domain(courses.begin(),courses.end());if(domain.size()!=courses.size()||domain.count(\"\")!=0U)return std::nullopt;std::map<std::string,std::set<std::string>> edges;std::map<std::string,std::size_t> indegree;for(const auto& c:courses)indegree[c]=0;std::set<std::pair<std::string,std::string>> seen;for(const auto& p:prerequisites){if(p.course==p.prerequisite||domain.count(p.course)==0U||domain.count(p.prerequisite)==0U||!seen.emplace(p.prerequisite,p.course).second)return std::nullopt;edges[p.prerequisite].insert(p.course);++indegree[p.course];}std::set<std::string> ready;for(const auto& item:indegree)if(item.second==0U)ready.insert(item.first);std::vector<std::vector<std::string>> plan;std::size_t done=0;while(!ready.empty()){std::vector<std::string> semester;for(std::size_t i=0;i<max_per_semester&&!ready.empty();++i){semester.push_back(*ready.begin());ready.erase(ready.begin());}for(const auto& course:semester)for(const auto& next:edges[course])if(--indegree[next]==0U)ready.insert(next);done+=semester.size();plan.push_back(semester);}if(done!=courses.size())return std::optional<std::vector<std::vector<std::string>>>{};return plan;",
        "auto r=prerequisite_semester_plan({\"a\",\"b\",\"c\"},{{\"c\",\"a\"}},2);require_case(r&&*r&&**r==std::vector<std::vector<std::string>>({{\"a\",\"b\"},{\"c\"}}));auto cycle=prerequisite_semester_plan({\"a\",\"b\"},{{\"a\",\"b\"},{\"b\",\"a\"}},2);require_case(cycle&&!*cycle);require_case(prerequisite_semester_plan({}, {},1)->value().empty());require_case(!prerequisite_semester_plan({\"a\"},{},0));require_case(!prerequisite_semester_plan({\"a\"},{{\"a\",\"x\"}},1));",
        "semester capacity is positive|ready ties use lexical course IDs|newly unlocked courses wait until the next semester|cycles are distinct from invalid inputs|empty curricula have no semesters",
        "capacity-batched lexical topological traversal with semester barriers",
    )
    add(
        "Grade School", "exam-room-interval-coloring", "Exam room interval coloring",
        "Assign half-open exam intervals to the minimum number of rooms. Exam IDs are unique and nonempty, times are nonnegative with start<end. Process intervals by start, then end, then ID; reuse the lowest numbered room whose prior exam ended by the new start. Return assignments ordered by exam ID and the room count.",
        "struct ExamInterval { std::string id; int start; int end; }; struct RoomAssignment { std::string id; std::size_t room; }; struct ExamRooms { std::size_t room_count; std::vector<RoomAssignment> assignments; };",
        "std::optional<ExamRooms> assign_exam_rooms(std::vector<ExamInterval> exams)",
        "std::set<std::string> ids;for(const auto& e:exams)if(e.id.empty()||e.start<0||e.start>=e.end||!ids.insert(e.id).second)return std::nullopt;std::sort(exams.begin(),exams.end(),[](const auto& a,const auto& b){return std::tie(a.start,a.end,a.id)<std::tie(b.start,b.end,b.id);});std::vector<int> available_at;std::vector<RoomAssignment> out;for(const auto& exam:exams){std::size_t room=available_at.size();for(std::size_t i=0;i<available_at.size();++i)if(available_at[i]<=exam.start){room=i;break;}if(room==available_at.size())available_at.push_back(exam.end);else available_at[room]=exam.end;out.push_back({exam.id,room});}std::sort(out.begin(),out.end(),[](const auto& a,const auto& b){return a.id<b.id;});return ExamRooms{available_at.size(),out};",
        "auto r=assign_exam_rooms({{\"b\",0,2},{\"a\",1,3},{\"c\",2,4}});require_case(r&&r->room_count==2U&&r->assignments.at(0).id==\"a\"&&r->assignments.at(2).room==0U);require_case(assign_exam_rooms({})->room_count==0U);require_case(assign_exam_rooms({{\"a\",0,1},{\"b\",1,2}})->room_count==1U);require_case(!assign_exam_rooms({{\"\",0,1}}));require_case(!assign_exam_rooms({{\"a\",1,1}}));",
        "intervals are half open|lowest reusable room wins|room numbers start at zero|final assignments are ordered by ID|invalid intervals reject atomically",
        "canonical interval partitioning with lowest-index reusable resource selection",
    )

    # Kindergarten Garden: coverage, monotone shade, and rectangle chemistry
    # use unrelated greedy, stack, and prefix-sum mechanisms.
    add(
        "Kindergarten Garden", "minimum-sprinkler-cover", "Minimum sprinkler cover",
        "Cover the closed integer bed segment [0,length] with the fewest sprinkler intervals. Sprinklers have unique nonempty IDs, nonnegative center and radius, and are clipped to the bed. At each uncovered point choose the reachable sprinkler extending farthest, breaking ties by ID. Return selected IDs or an empty inner value if coverage is impossible.",
        "struct Sprinkler { std::string id; int center; int radius; };",
        "std::optional<std::optional<std::vector<std::string>>> minimum_sprinkler_cover(int length, const std::vector<Sprinkler>& sprinklers)",
        "if(length<0)return std::nullopt;struct Span{std::string id;int begin;int end;};std::vector<Span> spans;std::set<std::string> ids;for(const auto& s:sprinklers){if(s.id.empty()||s.center<0||s.radius<0||!ids.insert(s.id).second)return std::nullopt;spans.push_back({s.id,std::max(0,s.center-s.radius),std::min(length,s.center+s.radius)});}std::vector<std::string> out;int covered=0;while(covered<length){const Span* best=nullptr;for(const auto& span:spans)if(span.begin<=covered&&span.end>covered&&(!best||span.end>best->end||(span.end==best->end&&span.id<best->id)))best=&span;if(!best)return std::optional<std::vector<std::string>>{};out.push_back(best->id);covered=best->end;}return out;",
        "auto r=minimum_sprinkler_cover(10,{{\"a\",2,3},{\"b\",7,3},{\"c\",5,1}});require_case(r&&*r&&**r==std::vector<std::string>({\"a\",\"b\"}));require_case(minimum_sprinkler_cover(0,{})->value().empty());auto no=minimum_sprinkler_cover(5,{{\"a\",1,1}});require_case(no&&!*no);require_case(!minimum_sprinkler_cover(-1,{}));require_case(!minimum_sprinkler_cover(2,{{\"a\",1,-1}}));",
        "the bed endpoints are closed|intervals clip to the bed|farthest reach is the greedy objective|ID breaks equal-reach ties|zero-length beds need no sprinklers",
        "left-frontier greedy interval cover with deterministic farthest-reach selection",
    )
    add(
        "Kindergarten Garden", "eastward-shade-spans", "Eastward shade spans",
        "For each positive plant height, return how many immediately eastward plants remain strictly shorter before the first height greater than or equal to it; count the garden edge when none blocks. Heights are positive and at most one million plants are allowed.",
        "",
        "std::optional<std::vector<std::size_t>> eastward_shade_spans(const std::vector<int>& heights)",
        "if(heights.size()>1000000U||std::any_of(heights.begin(),heights.end(),[](int h){return h<=0;}))return std::nullopt;std::vector<std::size_t> out(heights.size()),stack;for(std::size_t i=0;i<heights.size();++i){while(!stack.empty()&&heights[i]>=heights[stack.back()]){const auto index=stack.back();stack.pop_back();out[index]=i-index-1U;}stack.push_back(i);}while(!stack.empty()){const auto index=stack.back();stack.pop_back();out[index]=heights.size()-index-1U;}return out;",
        "require_case(eastward_shade_spans({5,3,4,2})->operator==(std::vector<std::size_t>({3,0,1,0})));require_case(eastward_shade_spans({1,2,3})->operator==(std::vector<std::size_t>({0,0,0})));require_case(eastward_shade_spans({3,2,1})->operator==(std::vector<std::size_t>({2,1,0})));require_case(eastward_shade_spans({})->empty());require_case(!eastward_shade_spans({1,0}));",
        "equal height blocks shade|the blocking plant is not counted|the edge acts after the final plant|output aligns with input indices|heights must be positive",
        "monotone decreasing index stack with blocker-triggered span finalization",
    )
    add(
        "Kindergarten Garden", "soil-rectangle-balances", "Soil rectangle balances",
        "Build nutrient balances for rectangular half-open queries over an integer soil grid. The grid must be nonempty rectangular with at most one million cells. Query bounds satisfy top<=bottom<=rows and left<=right<=columns. Return checked long long sums in query order, including zero for empty rectangles.",
        "struct SoilRectangle { std::size_t top; std::size_t left; std::size_t bottom; std::size_t right; };",
        "std::optional<std::vector<long long>> soil_rectangle_balances(const std::vector<std::vector<int>>& soil, const std::vector<SoilRectangle>& queries)",
        "if(soil.empty()||soil[0].empty()||soil.size()>1000000U/soil[0].size())return std::nullopt;const std::size_t rows=soil.size(),columns=soil[0].size();for(const auto& row:soil)if(row.size()!=columns)return std::nullopt;std::vector<std::vector<long long>> prefix(rows+1,std::vector<long long>(columns+1));for(std::size_t r=0;r<rows;++r)for(std::size_t c=0;c<columns;++c){const long double value=static_cast<long double>(soil[r][c])+prefix[r][c+1]+prefix[r+1][c]-prefix[r][c];if(value<std::numeric_limits<long long>::min()||value>std::numeric_limits<long long>::max())return std::nullopt;prefix[r+1][c+1]=static_cast<long long>(value);}std::vector<long long> out;for(const auto& q:queries){if(q.top>q.bottom||q.left>q.right||q.bottom>rows||q.right>columns)return std::nullopt;out.push_back(prefix[q.bottom][q.right]-prefix[q.top][q.right]-prefix[q.bottom][q.left]+prefix[q.top][q.left]);}return out;",
        "auto r=soil_rectangle_balances({{1,2},{3,4}},{{0,0,2,2},{0,1,2,2},{1,1,1,2}});require_case(r&&*r==std::vector<long long>({10,6,0}));require_case(!soil_rectangle_balances({},{}));require_case(!soil_rectangle_balances({{}},{}));require_case(!soil_rectangle_balances({{1},{2,3}},{}));require_case(!soil_rectangle_balances({{1}},{{0,0,2,1}}));",
        "queries are half open|empty rectangles sum to zero|query order is preserved|grid shape is validated once|prefix arithmetic is checked",
        "two-dimensional checked prefix construction with constant-time inclusion-exclusion queries",
    )

    # Linked List: all three references own and rewire unique_ptr nodes; their
    # partition, alternating merge, and suffix-dominance flows are distinct.
    add(
        "Linked List", "stable-chain-partition", "Stable chain partition",
        "Rewire an owned singly linked chain so nodes with value below pivot precede all remaining nodes while preserving relative order inside both groups. Reuse every existing node exactly once and allocate no replacement nodes.",
        "struct PartitionNode { int value; std::unique_ptr<PartitionNode> next; explicit PartitionNode(int v):value(v),next(nullptr){} };",
        "std::unique_ptr<PartitionNode> stable_chain_partition(std::unique_ptr<PartitionNode> head, int pivot)",
        "std::unique_ptr<PartitionNode> low,high;PartitionNode* low_tail=nullptr;PartitionNode* high_tail=nullptr;while(head){auto node=std::move(head);head=std::move(node->next);node->next=nullptr;if(node->value<pivot){PartitionNode* raw=node.get();if(low_tail)low_tail->next=std::move(node);else low=std::move(node);low_tail=raw;}else{PartitionNode* raw=node.get();if(high_tail)high_tail->next=std::move(node);else high=std::move(node);high_tail=raw;}}if(!low)return high;low_tail->next=std::move(high);return low;",
        "auto make=[](std::vector<int> values){std::unique_ptr<PartitionNode> head;PartitionNode* tail=nullptr;for(int v:values){auto node=std::make_unique<PartitionNode>(v);auto* raw=node.get();if(tail)tail->next=std::move(node);else head=std::move(node);tail=raw;}return head;};auto values=[](const auto& head){std::vector<int> out;for(auto* p=head.get();p;p=p->next.get())out.push_back(p->value);return out;};auto r=stable_chain_partition(make({3,1,4,2}),3);require_case(values(r)==std::vector<int>({1,2,3,4}));require_case(!stable_chain_partition(nullptr,0));auto all=stable_chain_partition(make({1,2}),5);require_case(values(all)==std::vector<int>({1,2}));auto none=stable_chain_partition(make({5,6}),5);require_case(values(none)==std::vector<int>({5,6}));",
        "nodes below pivot are stable|nodes at pivot join the high group|every input node remains present|empty input stays empty|ownership is transferred without copying nodes",
        "two owned tail chains joined after stable destructive partitioning",
    )
    add(
        "Linked List", "alternating-owned-merge", "Alternating owned merge",
        "Merge two owned singly linked chains by taking one node from first, then one from second, until both are exhausted. Remaining nodes from the longer input continue in order. Reuse nodes, preserve values, and begin with first even when it is empty.",
        "struct MergeNode { int value; std::unique_ptr<MergeNode> next; explicit MergeNode(int v):value(v),next(nullptr){} };",
        "std::unique_ptr<MergeNode> alternating_owned_merge(std::unique_ptr<MergeNode> first, std::unique_ptr<MergeNode> second)",
        "std::unique_ptr<MergeNode> out;MergeNode* tail=nullptr;bool take_first=true;while(first||second){std::unique_ptr<MergeNode> node;if((take_first&&first)||!second){node=std::move(first);first=std::move(node->next);}else{node=std::move(second);second=std::move(node->next);}node->next=nullptr;auto* raw=node.get();if(tail)tail->next=std::move(node);else out=std::move(node);tail=raw;take_first=!take_first;}return out;",
        "auto make=[](std::vector<int> values){std::unique_ptr<MergeNode> head;MergeNode* tail=nullptr;for(int v:values){auto node=std::make_unique<MergeNode>(v);auto* raw=node.get();if(tail)tail->next=std::move(node);else head=std::move(node);tail=raw;}return head;};auto values=[](const auto& head){std::vector<int> out;for(auto* p=head.get();p;p=p->next.get())out.push_back(p->value);return out;};auto r=alternating_owned_merge(make({1,3,5}),make({2,4}));require_case(values(r)==std::vector<int>({1,2,3,4,5}));auto left=alternating_owned_merge(make({1}),nullptr);require_case(values(left)==std::vector<int>({1}));auto right=alternating_owned_merge(nullptr,make({2,3}));require_case(values(right)==std::vector<int>({2,3}));require_case(!alternating_owned_merge(nullptr,nullptr));",
        "the first available node is preferred|selection alternates while both inputs remain|longer tails retain order|nodes are reused|two empty inputs yield an empty chain",
        "destructive two-source node detachment with alternating tail append",
    )
    add(
        "Linked List", "suffix-dominated-pruning", "Suffix dominated pruning",
        "Remove every node that has a strictly larger value somewhere to its right. Equal values do not dominate one another. Preserve original order among retained nodes and reuse their ownership. The implementation must operate by link rewiring, not by returning a separate value list.",
        "struct PruneNode { int value; std::unique_ptr<PruneNode> next; explicit PruneNode(int v):value(v),next(nullptr){} };",
        "std::unique_ptr<PruneNode> prune_suffix_dominated(std::unique_ptr<PruneNode> head)",
        "std::unique_ptr<PruneNode> reversed;while(head){auto node=std::move(head);head=std::move(node->next);node->next=std::move(reversed);reversed=std::move(node);}std::unique_ptr<PruneNode> kept;int maximum=std::numeric_limits<int>::min();while(reversed){auto node=std::move(reversed);reversed=std::move(node->next);if(node->value>=maximum){maximum=node->value;node->next=std::move(kept);kept=std::move(node);}}return kept;",
        "auto make=[](std::vector<int> values){std::unique_ptr<PruneNode> head;PruneNode* tail=nullptr;for(int v:values){auto node=std::make_unique<PruneNode>(v);auto* raw=node.get();if(tail)tail->next=std::move(node);else head=std::move(node);tail=raw;}return head;};auto values=[](const auto& head){std::vector<int> out;for(auto* p=head.get();p;p=p->next.get())out.push_back(p->value);return out;};auto r=prune_suffix_dominated(make({12,15,10,11,5,6,2,3}));require_case(values(r)==std::vector<int>({15,11,6,3}));auto equal=prune_suffix_dominated(make({2,2,1}));require_case(values(equal)==std::vector<int>({2,2,1}));require_case(!prune_suffix_dominated(nullptr));auto increasing=prune_suffix_dominated(make({1,2,3}));require_case(values(increasing)==std::vector<int>({3}));",
        "domination is strict|the last node always remains|retained order matches the input|negative values are supported|nodes are removed through ownership rewiring",
        "full chain reversal, running suffix maximum filter, and order-restoring prepend",
    )

    # Parallel Letter Frequency: prefix monoids, transition matrices, and
    # document-level rare-letter votes have separate shard result types.
    add(
        "Parallel Letter Frequency", "parallel-bracket-prefix-monoids", "Parallel bracket prefix monoids",
        "Validate a concatenation of text fragments as balanced parentheses while ignoring all non-parenthesis bytes. Use worker_count asynchronous contiguous shards. Each shard reports net balance and minimum relative prefix; combine shards in fragment order. worker_count is positive and no greater than the nonempty fragment count, except empty input accepts any positive worker count.",
        "struct BracketBalance { bool balanced; long long final_balance; long long minimum_prefix; };",
        "std::optional<BracketBalance> parallel_bracket_balance(const std::vector<std::string>& fragments, std::size_t worker_count)",
        "if(worker_count==0||(!fragments.empty()&&worker_count>fragments.size()))return std::nullopt;if(fragments.empty())return BracketBalance{true,0,0};using Summary=std::pair<long long,long long>;std::vector<std::future<Summary>> jobs;for(std::size_t w=0;w<worker_count;++w){const std::size_t begin=fragments.size()*w/worker_count,end=fragments.size()*(w+1U)/worker_count;jobs.push_back(std::async(std::launch::async,[&,begin,end]{long long balance=0,minimum=0;for(std::size_t i=begin;i<end;++i)for(char c:fragments[i])if(c=='('){++balance;}else if(c==')'){--balance;minimum=std::min(minimum,balance);}return Summary{balance,minimum};}));}long long balance=0,minimum=0;for(auto& job:jobs){const auto part=job.get();minimum=std::min(minimum,balance+part.second);balance+=part.first;}return BracketBalance{balance==0&&minimum>=0,balance,minimum};",
        "auto r=parallel_bracket_balance({\"(()\",\")x\",\"()\"},2);require_case(r&&r->balanced&&r->final_balance==0&&r->minimum_prefix==0);auto bad=parallel_bracket_balance({\")\",\"(\"},2);require_case(bad&&!bad->balanced&&bad->minimum_prefix==-1);require_case(parallel_bracket_balance({},3)->balanced);require_case(!parallel_bracket_balance({\"()\"},0));require_case(!parallel_bracket_balance({\"()\"},2));",
        "non-parenthesis bytes are ignored|shards are contiguous|combination follows source order|negative prefixes invalidate balance|empty input remains balanced",
        "asynchronous contiguous prefix-monoid summaries with ordered offset composition",
    )
    add(
        "Parallel Letter Frequency", "parallel-letter-transition-matrix", "Parallel letter transition matrix",
        "Count adjacent normalized ASCII-letter transitions within each input string using strided asynchronous workers. Nonletters are ignored without breaking adjacency, uppercase folds to lowercase, and transitions never cross string boundaries. Return a 26x26 row-major uint64 matrix. worker_count is positive and may exceed input count.",
        "",
        "std::optional<std::array<std::uint64_t,676>> parallel_letter_transitions(const std::vector<std::string>& inputs, std::size_t worker_count)",
        "if(worker_count==0)return std::nullopt;const std::size_t workers=std::min(worker_count,std::max<std::size_t>(1,inputs.size()));std::vector<std::future<std::array<std::uint64_t,676>>> jobs;for(std::size_t w=0;w<workers;++w)jobs.push_back(std::async(std::launch::async,[&,w]{std::array<std::uint64_t,676> local{};for(std::size_t i=w;i<inputs.size();i+=workers){int previous=-1;for(unsigned char c:inputs[i]){int current=-1;if(c>='A'&&c<='Z')current=c-'A';else if(c>='a'&&c<='z')current=c-'a';if(current>=0){if(previous>=0)++local[static_cast<std::size_t>(previous*26+current)];previous=current;}}}return local;}));std::array<std::uint64_t,676> out{};for(auto& job:jobs){const auto local=job.get();for(std::size_t i=0;i<out.size();++i){if(out[i]>std::numeric_limits<std::uint64_t>::max()-local[i])return std::nullopt;out[i]+=local[i];}}return out;",
        "auto r=parallel_letter_transitions({\"A-bA\",\"ab\"},2);require_case(r&&r->at(1)==2U&&r->at(26)==1U);auto e=parallel_letter_transitions({},8);require_case(e&&std::accumulate(e->begin(),e->end(),std::uint64_t{0})==0U);require_case(!parallel_letter_transitions({},0));require_case(parallel_letter_transitions({\"123\"},1)->at(0)==0U);require_case(parallel_letter_transitions({\"a\",\"b\"},1)->at(1)==0U);",
        "case folds to ASCII lowercase|nonletters do not reset adjacency|strings remain transition boundaries|worker excess is allowed|the merge is checked and deterministic",
        "strided asynchronous fixed-matrix accumulation with checked indexwise reduction",
    )
    add(
        "Parallel Letter Frequency", "parallel-rare-letter-votes", "Parallel rare letter votes",
        "For each input document, identify the ASCII letters whose document-local frequency is positive and minimal; give each such letter one vote. Count votes across documents in parallel and return positive vote counts ordered by descending votes then letter. Nonletters are ignored and worker_count is positive.",
        "struct LetterVote { char letter; std::size_t votes; };",
        "std::optional<std::vector<LetterVote>> parallel_rare_letter_votes(const std::vector<std::string>& documents, std::size_t worker_count)",
        "if(worker_count==0)return std::nullopt;const std::size_t workers=std::min(worker_count,std::max<std::size_t>(1,documents.size()));std::vector<std::future<std::array<std::size_t,26>>> jobs;for(std::size_t w=0;w<workers;++w)jobs.push_back(std::async(std::launch::async,[&,w]{std::array<std::size_t,26> votes{};for(std::size_t i=w;i<documents.size();i+=workers){std::array<std::size_t,26> counts{};for(unsigned char c:documents[i]){if(c>='A'&&c<='Z')++counts[c-'A'];else if(c>='a'&&c<='z')++counts[c-'a'];}std::size_t minimum=std::numeric_limits<std::size_t>::max();for(auto count:counts)if(count!=0U)minimum=std::min(minimum,count);if(minimum!=std::numeric_limits<std::size_t>::max())for(std::size_t j=0;j<26U;++j)if(counts[j]==minimum)++votes[j];}return votes;}));std::array<std::size_t,26> totals{};for(auto& job:jobs){const auto votes=job.get();for(std::size_t i=0;i<26U;++i)totals[i]+=votes[i];}std::vector<LetterVote> out;for(std::size_t i=0;i<26U;++i)if(totals[i]!=0U)out.push_back({static_cast<char>('a'+i),totals[i]});std::sort(out.begin(),out.end(),[](const auto& a,const auto& b){return a.votes!=b.votes?a.votes>b.votes:a.letter<b.letter;});return out;",
        "auto r=parallel_rare_letter_votes({\"aab\",\"bcc\",\"!!!\"},2);require_case(r&&r->size()==2U&&r->at(0).letter=='b'&&r->at(0).votes==2U&&r->at(1).letter=='a');require_case(parallel_rare_letter_votes({},4)->empty());require_case(!parallel_rare_letter_votes({},0));require_case(parallel_rare_letter_votes({\"Aa\"},1)->at(0).letter=='a');require_case(parallel_rare_letter_votes({\"123\"},1)->empty());",
        "votes are document-local|ties inside one document vote for every minimum|zero-frequency letters are excluded|case folds to lowercase|final ordering uses votes then letter",
        "parallel document-local minima extraction followed by deterministic vote aggregation",
    )

    # Phone Number: word segmentation, two-finger dialing, and strict masks
    # exercise DP, state-space optimization, and parser/formatter discipline.
    add(
        "Phone Number", "phoneword-segmentation", "Phoneword segmentation",
        "Segment a digit string 2..9 into dictionary words whose T9 encodings concatenate exactly to the digits. Dictionary words are unique lowercase ASCII letters. Minimize word count, then lexicographically compare the word vector. Return an empty inner value if no segmentation exists; input digits are nonempty and at most 64.",
        "",
        "std::optional<std::optional<std::vector<std::string>>> minimum_phoneword_segmentation(std::string_view digits, const std::vector<std::string>& dictionary)",
        "if(digits.empty()||digits.size()>64U||std::any_of(digits.begin(),digits.end(),[](char c){return c<'2'||c>'9';}))return std::nullopt;auto encode=[](const std::string& word){std::string out;for(unsigned char c:word){if(c<'a'||c>'z')return std::string{};const std::string groups=\"22233344455566677778889999\";out.push_back(groups[c-'a']);}return out;};std::set<std::string> seen;std::vector<std::pair<std::string,std::string>> words;for(const auto& word:dictionary){const auto code=encode(word);if(word.empty()||code.empty()||!seen.insert(word).second)return std::nullopt;words.push_back({word,code});}std::vector<std::optional<std::vector<std::string>>> best(digits.size()+1);best[0]=std::vector<std::string>{};for(std::size_t i=0;i<digits.size();++i)if(best[i])for(const auto& item:words)if(i+item.second.size()<=digits.size()&&digits.substr(i,item.second.size())==item.second){auto candidate=*best[i];candidate.push_back(item.first);auto& slot=best[i+item.second.size()];if(!slot||candidate.size()<slot->size()||(candidate.size()==slot->size()&&candidate<*slot))slot=candidate;}return best.back();",
        "auto r=minimum_phoneword_segmentation(\"228\",{\"cat\",\"bat\",\"a\",\"t\"});require_case(r&&*r&&**r==std::vector<std::string>({\"bat\"}));auto no=minimum_phoneword_segmentation(\"99\",{\"a\"});require_case(no&&!*no);require_case(!minimum_phoneword_segmentation(\"\",{}));require_case(!minimum_phoneword_segmentation(\"10\",{}));require_case(!minimum_phoneword_segmentation(\"2\",{\"A\"}));",
        "digits use only two through nine|fewest words is primary|lexical word vectors break ties|dictionary words are unique lowercase|impossible segmentation is not invalid input",
        "prefix dynamic programming over exact T9 dictionary encodings with canonical optimization",
    )
    add(
        "Phone Number", "two-finger-keypad-cost", "Two-finger keypad cost",
        "Compute the minimum Manhattan movement needed to dial a nonempty digit string on the standard 3x4 keypad with left finger initially on 4 and right finger on 6. Either finger may press each digit; pressing a current key costs zero. Return the minimum cost and a canonical L/R assignment, breaking cost ties lexicographically.",
        "struct FingerDial { int cost; std::string assignment; };",
        "std::optional<FingerDial> minimum_two_finger_dial(std::string_view digits)",
        "if(digits.empty()||std::any_of(digits.begin(),digits.end(),[](char c){return c<'0'||c>'9';}))return std::nullopt;const std::array<std::pair<int,int>,10> pos{{{3,1},{0,0},{0,1},{0,2},{1,0},{1,1},{1,2},{2,0},{2,1},{2,2}}};using State=std::pair<int,std::string>;std::map<std::pair<int,int>,State> states{{{4,6},{0,\"\"}}};auto distance=[&](int a,int b){return std::abs(pos[a].first-pos[b].first)+std::abs(pos[a].second-pos[b].second);};for(char c:digits){const int key=c-'0';std::map<std::pair<int,int>,State> next;for(const auto& item:states){const int left=item.first.first,right=item.first.second;for(char hand:{'L','R'}){const auto state=hand=='L'?std::pair<int,int>{key,right}:std::pair<int,int>{left,key};State candidate{item.second.first+distance(hand=='L'?left:right,key),item.second.second+hand};auto it=next.find(state);if(it==next.end()||candidate.first<it->second.first||(candidate.first==it->second.first&&candidate.second<it->second.second))next[state]=candidate;}}states=std::move(next);}std::optional<State> best;for(const auto& item:states)if(!best||item.second.first<best->first||(item.second.first==best->first&&item.second.second<best->second))best=item.second;return FingerDial{best->first,best->second};",
        "auto r=minimum_two_finger_dial(\"46\");require_case(r&&r->cost==0&&r->assignment==\"LR\");auto one=minimum_two_finger_dial(\"5\");require_case(one&&one->cost==1&&one->assignment==\"L\");require_case(!minimum_two_finger_dial(\"\"));require_case(!minimum_two_finger_dial(\"1a\"));require_case(minimum_two_finger_dial(\"44\")->cost==0);",
        "keypad coordinates are fixed|either finger may press every digit|assignment length equals digit length|cost ties use lexical L before R|initial positions are part of the contract",
        "dynamic programming over ordered two-finger positions with path-string tie resolution",
    )
    add(
        "Phone Number", "strict-number-mask-format", "Strict number mask format",
        "Format an exact digit string with a mask containing D placeholders, literal spaces, plus, hyphen, parentheses, and dots. The number of D placeholders must equal the digit count; digits must be nonempty and decimal. A backslash escapes one following allowed literal and may not escape D. Return the formatted bytes exactly.",
        "",
        "std::optional<std::string> strict_number_mask_format(std::string_view digits, std::string_view mask)",
        "if(digits.empty()||std::any_of(digits.begin(),digits.end(),[](char c){return c<'0'||c>'9';}))return std::nullopt;std::string out;std::size_t index=0;auto literal=[](char c){return c==' '||c=='+'||c=='-'||c=='('||c==')'||c=='.';};for(std::size_t i=0;i<mask.size();++i){char c=mask[i];if(c=='D'){if(index>=digits.size())return std::nullopt;out.push_back(digits[index++]);}else if(c=='\\'){if(++i>=mask.size()||mask[i]=='D'||!literal(mask[i]))return std::nullopt;out.push_back(mask[i]);}else{if(!literal(c))return std::nullopt;out.push_back(c);}}if(index!=digits.size())return std::nullopt;return out;",
        "require_case(strict_number_mask_format(\"1234\",\"(DD) DD\")==\"(12) 34\");require_case(strict_number_mask_format(\"12\",\"+D-D\")==\"+1-2\");require_case(!strict_number_mask_format(\"\",\"\"));require_case(!strict_number_mask_format(\"12\",\"D\"));require_case(!strict_number_mask_format(\"1\",\"X\"));",
        "D is the only placeholder|placeholder count is exact|literals use a closed alphabet|escaping a placeholder is forbidden|formatted bytes preserve the mask",
        "single-pass closed-grammar mask parser with synchronized digit consumption",
    )

    # Spiral Matrix: diagonal algebra, prime-corner analysis, and variable-step
    # corner generation avoid rectangular matrix materialization.
    add(
        "Spiral Matrix", "odd-spiral-diagonal-sum", "Odd spiral diagonal sum",
        "Return the sum of both diagonals in an outward clockwise square number spiral with 1 at the center and consecutive integers, for an odd positive side length at most 1000001. Use checked uint64 arithmetic and count the center once.",
        "",
        "std::optional<std::uint64_t> odd_spiral_diagonal_sum(std::uint64_t side)",
        "if(side==0U||side%2U==0U||side>1000001U)return std::nullopt;std::uint64_t sum=1;for(std::uint64_t length=3;length<=side;length+=2){const long double layer=4.0L*length*length-6.0L*(length-1U);if(layer>std::numeric_limits<std::uint64_t>::max()-sum)return std::nullopt;sum+=static_cast<std::uint64_t>(layer);}return sum;",
        "require_case(odd_spiral_diagonal_sum(1)==1U);require_case(odd_spiral_diagonal_sum(3)==25U);require_case(odd_spiral_diagonal_sum(5)==101U);require_case(!odd_spiral_diagonal_sum(0));require_case(!odd_spiral_diagonal_sum(4));",
        "side length is odd and positive|the center is counted once|each outer layer contributes four corners|work is proportional to side length|overflow rejects",
        "closed-form per-ring corner accumulation over odd side lengths",
    )
    add(
        "Spiral Matrix", "spiral-prime-corner-counts", "Spiral prime corner counts",
        "For every odd square side from 3 through max_side, count how many of that ring's four corner labels are prime in the standard consecutive outward spiral. max_side is odd, 3..10001. Return cumulative prime-corner and total-diagonal counts after each ring.",
        "struct PrimeCornerCount { std::uint64_t side; std::size_t cumulative_primes; std::size_t cumulative_diagonal_values; };",
        "std::optional<std::vector<PrimeCornerCount>> spiral_prime_corner_counts(std::uint64_t max_side)",
        "if(max_side<3U||max_side%2U==0U||max_side>10001U)return std::nullopt;auto prime=[](std::uint64_t value){if(value<2U)return false;for(std::uint64_t d=2;d<=value/d;++d)if(value%d==0U)return false;return true;};std::vector<PrimeCornerCount> out;std::size_t primes=0,total=1;for(std::uint64_t side=3;side<=max_side;side+=2){const std::uint64_t square=side*side,step=side-1U;for(std::uint64_t k=0;k<4U;++k)if(prime(square-k*step))++primes;total+=4U;out.push_back({side,primes,total});}return out;",
        "auto r=spiral_prime_corner_counts(5);require_case(r&&r->size()==2U&&r->at(0).cumulative_primes==3U&&r->at(0).cumulative_diagonal_values==5U&&r->at(1).cumulative_primes==5U);require_case(!spiral_prime_corner_counts(1));require_case(!spiral_prime_corner_counts(4));require_case(!spiral_prime_corner_counts(10003));require_case(spiral_prime_corner_counts(3)->at(0).side==3U);",
        "one center value starts the total|four new corners appear per ring|primality is exact integer trial division|counts are cumulative|the side domain is bounded",
        "odd-ring corner arithmetic with exact bounded primality classification",
    )
    add(
        "Spiral Matrix", "variable-step-spiral-corners", "Variable-step spiral corners",
        "Generate four corner labels for each outward square spiral ring. Start with center, and on ring r advance through four sides of length 2r; each cell on that ring adds ring_steps[r-1] to the current label. ring_steps is nonempty, positive, at most 10000 entries, and checked signed arithmetic is required.",
        "",
        "std::optional<std::vector<std::array<long long,4>>> variable_step_spiral_corners(long long center, const std::vector<long long>& ring_steps)",
        "if(ring_steps.empty()||ring_steps.size()>10000U||std::any_of(ring_steps.begin(),ring_steps.end(),[](long long step){return step<=0;}))return std::nullopt;std::vector<std::array<long long,4>> out;long long current=center;for(std::size_t ring=1;ring<=ring_steps.size();++ring){std::array<long long,4> corners{};const long long step=ring_steps[ring-1];for(std::size_t side=0;side<4U;++side){for(std::size_t cell=0;cell<2U*ring;++cell){if(current>std::numeric_limits<long long>::max()-step)return std::nullopt;const long long next=current+step;current=next;}corners[side]=current;}out.push_back(corners);}return out;",
        "auto r=variable_step_spiral_corners(1,{1,2});require_case(r&&r->at(0)==std::array<long long,4>({3,5,7,9})&&r->at(1)==std::array<long long,4>({17,25,33,41}));require_case(!variable_step_spiral_corners(0,{}));require_case(!variable_step_spiral_corners(0,{0}));require_case(!variable_step_spiral_corners(std::numeric_limits<long long>::max(),{1}));require_case(variable_step_spiral_corners(-10,{1})->at(0).back()==-2);",
        "each ring has four equal side lengths|ring-specific steps are constant within a ring|corner order follows outward traversal|signed centers are valid|overflow rejects before wraparound",
        "nested ring-side-cell accumulation with checked variable per-ring increments",
    )

    # Sublist: affine windows, compressed windows, and dominance subsequences
    # deliberately use algebraic, run-index, and dynamic-programming oracles.
    add(
        "Sublist", "affine-slice-matches", "Affine slice matches",
        "Find every contiguous slice of values that equals scale*pattern+offset elementwise for integral scale and offset. pattern must contain at least two values and at least one unequal pair so scale is uniquely determined. Return matches ordered by start, each with its exact scale and offset; checked long long arithmetic is required.",
        "struct AffineSliceMatch { std::size_t start; long long scale; long long offset; };",
        "std::optional<std::vector<AffineSliceMatch>> affine_slice_matches(const std::vector<long long>& values, const std::vector<long long>& pattern)",
        "if(pattern.size()<2U)return std::nullopt;std::size_t pivot=1;while(pivot<pattern.size()&&pattern[pivot]==pattern[0])++pivot;if(pivot==pattern.size())return std::nullopt;std::vector<AffineSliceMatch> out;if(pattern.size()>values.size())return out;for(std::size_t start=0;start+pattern.size()<=values.size();++start){const long long denominator=pattern[pivot]-pattern[0],numerator=values[start+pivot]-values[start];if(denominator==0||numerator%denominator!=0)continue;const long long scale=numerator/denominator;const long double raw_offset=static_cast<long double>(values[start])-static_cast<long double>(scale)*pattern[0];if(raw_offset<std::numeric_limits<long long>::min()||raw_offset>std::numeric_limits<long long>::max())return std::nullopt;const long long offset=static_cast<long long>(raw_offset);bool ok=true;for(std::size_t i=0;i<pattern.size();++i){const long double expected=static_cast<long double>(scale)*pattern[i]+offset;if(expected<std::numeric_limits<long long>::min()||expected>std::numeric_limits<long long>::max()||values[start+i]!=static_cast<long long>(expected)){ok=false;break;}}if(ok)out.push_back({start,scale,offset});}return out;",
        "auto r=affine_slice_matches({9,11,13,0,5,8},{2,3,4});require_case(r&&r->size()==1U&&r->at(0).start==0U&&r->at(0).scale==2&&r->at(0).offset==5);auto neg=affine_slice_matches({3,2,1},{1,2,3});require_case(neg&&neg->at(0).scale==-1&&neg->at(0).offset==4);require_case(!affine_slice_matches({1},{1}));require_case(!affine_slice_matches({1,1},{2,2}));require_case(affine_slice_matches({1},{1,2})->empty());",
        "scale and offset are integral|a nonconstant pattern is required|negative scales are valid|matches are ordered by start|overflow rejects rather than rounding",
        "per-origin affine parameter inference followed by exact checked window verification",
    )
    add(
        "Sublist", "compressed-run-pattern-matches", "Compressed run pattern matches",
        "Find every expanded start offset at which an uncompressed pattern occurs in a canonical run-length sequence, without materializing the expanded source. Runs have positive counts, adjacent values differ, total expanded length is at most one million, and pattern is nonempty. Return offsets in ascending order.",
        "struct ValueRun { int value; std::size_t count; };",
        "std::optional<std::vector<std::size_t>> compressed_run_pattern_matches(const std::vector<ValueRun>& runs, const std::vector<int>& pattern)",
        "if(pattern.empty())return std::nullopt;std::vector<std::size_t> ends;std::size_t total=0;for(std::size_t i=0;i<runs.size();++i){if(runs[i].count==0U||(i>0&&runs[i-1].value==runs[i].value)||runs[i].count>1000000U-total)return std::nullopt;total+=runs[i].count;ends.push_back(total);}std::vector<std::size_t> out;if(pattern.size()>total)return out;auto value_at=[&](std::size_t index){const auto it=std::upper_bound(ends.begin(),ends.end(),index);return runs[static_cast<std::size_t>(it-ends.begin())].value;};for(std::size_t start=0;start+pattern.size()<=total;++start){bool ok=true;for(std::size_t i=0;i<pattern.size();++i)if(value_at(start+i)!=pattern[i]){ok=false;break;}if(ok)out.push_back(start);}return out;",
        "auto r=compressed_run_pattern_matches({{1,3},{2,2},{1,1}},{1,2});require_case(r&&*r==std::vector<std::size_t>({2}));auto same=compressed_run_pattern_matches({{4,3}},{4,4});require_case(same&&*same==std::vector<std::size_t>({0,1}));require_case(!compressed_run_pattern_matches({},{}));require_case(!compressed_run_pattern_matches({{1,0}},{1}));require_case(!compressed_run_pattern_matches({{1,1},{1,2}},{1}));",
        "source runs are canonical|matches may cross run boundaries|overlapping matches are retained|offsets refer to expanded positions|expanded length is bounded without expansion",
        "prefix-end indexed virtual access with complete bounded start verification",
    )
    add(
        "Sublist", "dominance-subsequence-witness", "Dominance subsequence witness",
        "Return one longest subsequence of point indices whose x coordinates strictly increase and y coordinates strictly decrease. Preserve source order, accept at most 2000 points, and break equal-length choices by lexicographically smallest index vector. Empty input yields an empty witness.",
        "struct DominancePoint { int x; int y; };",
        "std::optional<std::vector<std::size_t>> dominance_subsequence_witness(const std::vector<DominancePoint>& points)",
        "if(points.size()>2000U)return std::nullopt;std::vector<std::vector<std::size_t>> best(points.size());std::vector<std::size_t> answer;for(std::size_t i=0;i<points.size();++i){best[i]={i};for(std::size_t j=0;j<i;++j)if(points[j].x<points[i].x&&points[j].y>points[i].y){auto candidate=best[j];candidate.push_back(i);if(candidate.size()>best[i].size()||(candidate.size()==best[i].size()&&candidate<best[i]))best[i]=std::move(candidate);}if(best[i].size()>answer.size()||(best[i].size()==answer.size()&&best[i]<answer))answer=best[i];}return answer;",
        "auto r=dominance_subsequence_witness({{1,5},{2,4},{2,3},{3,2}});require_case(r&&*r==std::vector<std::size_t>({0,1,3}));require_case(dominance_subsequence_witness({})->empty());require_case(dominance_subsequence_witness({{1,1}})->at(0)==0U);require_case(dominance_subsequence_witness({{2,1},{1,2}})->size()==1U);require_case(!dominance_subsequence_witness(std::vector<DominancePoint>(2001)));",
        "both coordinate inequalities are strict|source index order is preserved|witness indices are returned, not points|lexical indices break length ties|quadratic work is bounded",
        "index-vector dynamic programming with conjunctive dominance and canonical witness ties",
    )

    # Yacht: modular convolution, nontransitive tournaments, and arithmetic
    # expression closure are separate dice reasoning surfaces.
    add(
        "Yacht", "dice-modulo-distribution", "Dice modulo distribution",
        "Compute the exact distribution of the sum modulo modulus for independent dice whose faces are explicitly listed. Every die has 1..12 integer faces, at most twelve dice are allowed, modulus is 1..64, and face values may be negative. Return uint64 outcome counts indexed by residue with checked addition.",
        "",
        "std::optional<std::vector<std::uint64_t>> dice_modulo_distribution(const std::vector<std::vector<int>>& dice, int modulus)",
        "if(modulus<=0||modulus>64||dice.size()>12U)return std::nullopt;std::vector<std::uint64_t> counts(static_cast<std::size_t>(modulus));counts[0]=1;for(const auto& die:dice){if(die.empty()||die.size()>12U)return std::nullopt;std::vector<std::uint64_t> next(counts.size());for(std::size_t residue=0;residue<counts.size();++residue)for(int face:die){long long target=(static_cast<long long>(residue)+face)%modulus;if(target<0)target+=modulus;auto& slot=next[static_cast<std::size_t>(target)];if(slot>std::numeric_limits<std::uint64_t>::max()-counts[residue])return std::nullopt;slot+=counts[residue];}counts=std::move(next);}return counts;",
        "auto r=dice_modulo_distribution({{1,2},{1,2}},3);require_case(r&&*r==std::vector<std::uint64_t>({1,1,2}));auto empty=dice_modulo_distribution({},5);require_case(empty&&empty->at(0)==1U&&std::accumulate(empty->begin(),empty->end(),std::uint64_t{0})==1U);auto negative=dice_modulo_distribution({{-1}},5);require_case(negative&&negative->at(4)==1U);require_case(!dice_modulo_distribution({{}},3));require_case(!dice_modulo_distribution({},0));",
        "residues are canonical nonnegative indices|negative faces normalize correctly|zero dice have one empty outcome|face multiplicity affects counts|all additions are checked",
        "iterative modular convolution of explicit independent face distributions",
    )
    add(
        "Yacht", "nontransitive-dice-tournament", "Nontransitive dice tournament",
        "Compare every ordered pair of dice by counting face pairs on which the left die is greater, the right die is greater, or tied. Dice IDs are unique and nonempty, every die has 1..20 faces, and at most 32 dice are allowed. Return square matrices in input order with zero diagonal.",
        "struct LabeledDie { std::string id; std::vector<int> faces; }; struct DiceTournament { std::vector<std::vector<std::uint64_t>> wins; std::vector<std::vector<std::uint64_t>> losses; std::vector<std::vector<std::uint64_t>> ties; };",
        "std::optional<DiceTournament> nontransitive_dice_tournament(const std::vector<LabeledDie>& dice)",
        "if(dice.size()>32U)return std::nullopt;std::set<std::string> ids;for(const auto& die:dice)if(die.id.empty()||die.faces.empty()||die.faces.size()>20U||!ids.insert(die.id).second)return std::nullopt;const std::size_t n=dice.size();std::vector<std::vector<std::uint64_t>> wins(n,std::vector<std::uint64_t>(n)),losses=wins,ties=wins;for(std::size_t i=0;i<n;++i)for(std::size_t j=i+1;j<n;++j){std::uint64_t left=0,right=0,equal=0;for(int a:dice[i].faces)for(int b:dice[j].faces)if(a>b)++left;else if(a<b)++right;else ++equal;wins[i][j]=left;wins[j][i]=right;losses[i][j]=right;losses[j][i]=left;ties[i][j]=ties[j][i]=equal;}return DiceTournament{wins,losses,ties};",
        "auto r=nontransitive_dice_tournament({{\"a\",{1,4}},{\"b\",{2,3}}});require_case(r&&r->wins[0][1]==2U&&r->wins[1][0]==2U&&r->ties[0][1]==0U&&r->losses[0][1]==2U);require_case(nontransitive_dice_tournament({})->wins.empty());require_case(!nontransitive_dice_tournament({{\"\",{1}}}));require_case(!nontransitive_dice_tournament({{\"a\",{} }}));require_case(!nontransitive_dice_tournament({{\"a\",{1}},{\"a\",{2}}}));",
        "all face pairs are counted|ordered matrices transpose wins and losses|ties are symmetric|diagonals remain zero|input order defines matrix indices",
        "bounded pairwise Cartesian face comparison into reciprocal outcome matrices",
    )
    add(
        "Yacht", "dice-expression-values", "Dice expression values",
        "Return every integer obtainable by parenthesizing the dice values in source order and placing either addition or multiplication between adjacent groups. One through eight dice are required, each value is -20..20, and every intermediate result must fit in signed 32-bit. Return unique results ascending.",
        "",
        "std::optional<std::vector<int>> dice_expression_values(const std::vector<int>& dice)",
        "if(dice.empty()||dice.size()>8U||std::any_of(dice.begin(),dice.end(),[](int v){return v<-20||v>20;}))return std::nullopt;const std::size_t n=dice.size();std::vector<std::vector<std::set<int>>> dp(n,std::vector<std::set<int>>(n));for(std::size_t i=0;i<n;++i)dp[i][i].insert(dice[i]);for(std::size_t length=2;length<=n;++length)for(std::size_t begin=0;begin+length<=n;++begin){const std::size_t end=begin+length-1;for(std::size_t split=begin;split<end;++split)for(int left:dp[begin][split])for(int right:dp[split+1][end])for(long long value:{static_cast<long long>(left)+right,static_cast<long long>(left)*right})if(value>=std::numeric_limits<int>::min()&&value<=std::numeric_limits<int>::max())dp[begin][end].insert(static_cast<int>(value));}return std::vector<int>(dp[0][n-1].begin(),dp[0][n-1].end());",
        "auto r=dice_expression_values({1,2,3});require_case(r&&std::find(r->begin(),r->end(),9)!=r->end()&&std::find(r->begin(),r->end(),7)!=r->end()&&std::is_sorted(r->begin(),r->end()));require_case(dice_expression_values({5})->operator==(std::vector<int>({5})));require_case(!dice_expression_values({}));require_case(!dice_expression_values(std::vector<int>(9,1)));require_case(!dice_expression_values({21}));",
        "source order cannot change|both binary operations are available|every parenthesization is considered|overflowing intermediates are excluded|results are unique ascending",
        "interval dynamic-programming closure over ordered addition and multiplication compositions",
    )

    # Zebra Puzzle: alphametic arithmetic, nonogram placement, and skyscraper
    # visibility are three bounded, executable constraint systems.
    add(
        "Zebra Puzzle", "bounded-alphametic-count", "Bounded alphametic count",
        "Count base-10 assignments satisfying first+second=sum for uppercase-letter words. All distinct letters map to distinct digits, leading letters of multi-character words are nonzero, word lengths are 1..7, and at most eight distinct letters are allowed. Return the exact assignment count.",
        "",
        "std::optional<std::size_t> bounded_alphametic_count(std::string_view first, std::string_view second, std::string_view sum)",
        "auto valid=[](std::string_view word){return !word.empty()&&word.size()<=7U&&std::all_of(word.begin(),word.end(),[](char c){return c>='A'&&c<='Z';});};if(!valid(first)||!valid(second)||!valid(sum))return std::nullopt;std::set<char> domain;for(char c:first)domain.insert(c);for(char c:second)domain.insert(c);for(char c:sum)domain.insert(c);if(domain.size()>8U)return std::nullopt;std::vector<char> letters(domain.begin(),domain.end());std::set<char> leading;if(first.size()>1)leading.insert(first.front());if(second.size()>1)leading.insert(second.front());if(sum.size()>1)leading.insert(sum.front());std::array<int,26> value;value.fill(-1);std::array<unsigned char,10> used{};std::size_t count=0;std::function<void(std::size_t)> assign=[&](std::size_t index){if(index==letters.size()){auto number=[&](std::string_view word){long long out=0;for(char c:word)out=out*10+value[c-'A'];return out;};if(number(first)+number(second)==number(sum))++count;return;}const char letter=letters[index];for(int digit=0;digit<=9;++digit)if(!used[digit]&&(digit!=0||leading.count(letter)==0U)){used[digit]=1U;value[letter-'A']=digit;assign(index+1);used[digit]=0U;value[letter-'A']=-1;}};assign(0);return count;",
        "require_case(bounded_alphametic_count(\"A\",\"A\",\"B\")==4U);require_case(bounded_alphametic_count(\"A\",\"B\",\"A\")==0U);require_case(!bounded_alphametic_count(\"\",\"A\",\"B\"));require_case(!bounded_alphametic_count(\"a\",\"A\",\"B\"));require_case(!bounded_alphametic_count(\"ABCDEFG\",\"H\",\"IJ\"));",
        "letters map injectively to digits|multi-character leading letters are nonzero|the arithmetic equation is exact|the letter domain is bounded|zero solutions are valid",
        "lexical letter assignment backtracking with leading-zero and equation pruning",
    )
    add(
        "Zebra Puzzle", "nonogram-line-completion-count", "Nonogram line completion count",
        "Count binary line fillings of exact length matching ordered positive run clues. Line length is 0..60, at most fifteen clues are allowed, and the count must fit uint64. Runs are separated by at least one zero; an empty clue list describes the all-zero line.",
        "",
        "std::optional<std::uint64_t> nonogram_line_completion_count(std::size_t length, const std::vector<std::size_t>& clues)",
        "if(length>60U||clues.size()>15U||std::any_of(clues.begin(),clues.end(),[](std::size_t v){return v==0U;}))return std::nullopt;std::map<std::pair<std::size_t,std::size_t>,std::uint64_t> memo;std::function<std::optional<std::uint64_t>(std::size_t,std::size_t)> solve=[&](std::size_t clue,std::size_t position)->std::optional<std::uint64_t>{const auto key=std::make_pair(clue,position);auto found=memo.find(key);if(found!=memo.end())return found->second;if(clue==clues.size())return std::uint64_t{1};std::size_t remaining=0;for(std::size_t i=clue;i<clues.size();++i)remaining+=clues[i];remaining+=clues.size()-clue-1U;if(position+remaining>length)return std::uint64_t{0};std::uint64_t total=0;const std::size_t latest=length-remaining;for(std::size_t start=position;start<=latest;++start){const std::size_t next=start+clues[clue]+(clue+1U<clues.size()?1U:0U);auto child=solve(clue+1U,next);if(!child)return std::nullopt;if(total>std::numeric_limits<std::uint64_t>::max()-*child)return std::nullopt;total+=*child;}memo[key]=total;return total;};return solve(0,0);",
        "require_case(nonogram_line_completion_count(5,{2})==4U);require_case(nonogram_line_completion_count(5,{1,1})==6U);require_case(nonogram_line_completion_count(0,{})==1U);require_case(nonogram_line_completion_count(2,{3})==0U);require_case(!nonogram_line_completion_count(5,{0}));",
        "clue order is fixed|runs have a mandatory zero separator|unused cells are zero|empty clues have exactly one filling|impossible clues have zero fillings",
        "memoized ordered run-start placement with exact remaining-space bounds",
    )
    add(
        "Zebra Puzzle", "skyscraper-row-completions", "Skyscraper row completions",
        "Enumerate permutations of heights 1..size satisfying optional left and right visibility clues, where zero means unspecified. Size is 1..9 and clues are 0..size. Return matching rows in lexicographic order, capped by max_results; return an empty inner value when more than max_results exist so truncation is never mistaken for completeness.",
        "",
        "std::optional<std::optional<std::vector<std::vector<int>>>> skyscraper_row_completions(int size, int left_visible, int right_visible, std::size_t max_results)",
        "if(size<1||size>9||left_visible<0||left_visible>size||right_visible<0||right_visible>size||max_results==0)return std::nullopt;std::vector<int> row(static_cast<std::size_t>(size));std::iota(row.begin(),row.end(),1);std::vector<std::vector<int>> out;auto visible=[](auto begin,auto end){int maximum=0,count=0;for(auto it=begin;it!=end;++it)if(*it>maximum){maximum=*it;++count;}return count;};do{if((left_visible==0||visible(row.begin(),row.end())==left_visible)&&(right_visible==0||visible(row.rbegin(),row.rend())==right_visible)){if(out.size()==max_results)return std::optional<std::vector<std::vector<int>>>{};out.push_back(row);}}while(std::next_permutation(row.begin(),row.end()));return out;",
        "auto r=skyscraper_row_completions(3,3,1,10);require_case(r&&*r&&**r==std::vector<std::vector<int>>({{1,2,3}}));auto all=skyscraper_row_completions(2,0,0,2);require_case(all&&*all&&(**all).size()==2U);auto capped=skyscraper_row_completions(3,0,0,2);require_case(capped&&!*capped);require_case(!skyscraper_row_completions(0,0,0,1));require_case(!skyscraper_row_completions(3,4,0,1));",
        "height rows are permutations|zero clues are wildcards|visibility scans use strict record highs|result rows are lexical|cap excess yields no incomplete list",
        "lexical permutation enumeration with bidirectional visibility filtering and fail-closed cap",
    )

    if len(specs) != 51:
        raise ValueError(f"expected 51 q85 specs, got {len(specs)}")
    if tuple(dict.fromkeys(spec.topic for spec in specs)) != (
        "Allergies", "Bank Account", "Binary Search Tree", "Circular Buffer",
        "Clock", "Complex Numbers", "Crypto Square", "Diamond", "Grade School",
        "Kindergarten Garden", "Linked List", "Parallel Letter Frequency",
        "Phone Number", "Spiral Matrix", "Sublist", "Yacht", "Zebra Puzzle",
    ):
        raise ValueError("q85 topic registry/order mismatch")
    return specs
