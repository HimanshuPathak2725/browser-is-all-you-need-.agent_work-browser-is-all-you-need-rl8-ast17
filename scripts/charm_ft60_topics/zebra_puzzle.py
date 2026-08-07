"""Zebra-puzzle task definitions for the four-topic 60-task batch."""

from __future__ import annotations

from .common import TaskSpec


SPECS = (
    TaskSpec(
        "ac3-domain-reducer",
        r"""
namespace ac3_reducer {
std::optional<std::vector<std::vector<int>>> reduce(
    std::vector<std::vector<int>> domains,const std::vector<Arc>& arcs) {
    for(auto& domain:domains) {
        std::sort(domain.begin(),domain.end());
        domain.erase(std::unique(domain.begin(),domain.end()),domain.end());
        if(domain.empty()) return std::nullopt;
    }
    for(const auto& arc:arcs)
        if(arc.left<0||arc.right<0||arc.left>=static_cast<int>(domains.size())||
           arc.right>=static_cast<int>(domains.size())) throw std::invalid_argument("arc");
    std::deque<std::size_t> queue;
    for(std::size_t i=0;i<arcs.size();++i) queue.push_back(i);
    while(!queue.empty()) {
        const auto index=queue.front(); queue.pop_front();
        const auto& arc=arcs[index];
        auto& left=domains[static_cast<std::size_t>(arc.left)];
        const auto& right=domains[static_cast<std::size_t>(arc.right)];
        const auto old=left.size();
        left.erase(std::remove_if(left.begin(),left.end(),[&](int value) {
            return std::none_of(right.begin(),right.end(),[&](int other) {
                return std::find(arc.allowed.begin(),arc.allowed.end(),
                                 std::make_pair(value,other))!=arc.allowed.end();
            });
        }),left.end());
        if(left.empty()) return std::nullopt;
        if(left.size()!=old) for(std::size_t i=0;i<arcs.size();++i)
            if(arcs[i].right==arc.left && i!=index) queue.push_back(i);
    }
    return domains;
}
}
""",
        r"""
int main() {
    using ac3_reducer::Arc; using ac3_reducer::reduce;
    auto a=reduce({{1,1,2},{2}},{{0,1,{{1,2}}}});
    assert(a && (*a)[0]==std::vector<int>{1});
    assert(!reduce({{1},{2}},{{0,1,{}}}));
    auto b=reduce({{1,2},{1,2}},{{0,1,{{1,2},{2,1}}},{1,0,{{1,2},{2,1}}}});
    assert(b && (*b)[0].size()==2);
    assert(!reduce({{}, {1}},{}));
    bool bad=false; try { (void)reduce({{1}},{{0,2,{}}}); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "if(left.size()!=old)",
        "if(left.size()==old)",
        "ac3-reduction",
        ("arc-consistency", "support-check", "fixed-point"),
    ),
    TaskSpec(
        "hall-set-pruner",
        r"""
namespace hall_pruner {
std::optional<std::vector<std::vector<int>>> prune(std::vector<std::vector<int>> domains) {
    if(domains.size()>20) throw std::invalid_argument("variables");
    for(auto& domain:domains) {
        std::sort(domain.begin(),domain.end());
        domain.erase(std::unique(domain.begin(),domain.end()),domain.end());
        if(domain.empty()) return std::nullopt;
    }
    bool changed=true;
    while(changed) {
        changed=false;
        const std::uint64_t limit=std::uint64_t{1}<<domains.size();
        for(std::uint64_t subset=1;subset<limit;++subset) {
            std::set<int> values; std::size_t variables=0;
            for(std::size_t i=0;i<domains.size();++i) if(subset&(std::uint64_t{1}<<i)) {
                ++variables; values.insert(domains[i].begin(),domains[i].end());
            }
            if(values.size()<variables) return std::nullopt;
            if(values.size()==variables) for(std::size_t i=0;i<domains.size();++i)
                if(!(subset&(std::uint64_t{1}<<i))) {
                    const auto old=domains[i].size();
                    domains[i].erase(std::remove_if(domains[i].begin(),domains[i].end(),
                        [&](int value){return values.count(value)!=0;}),domains[i].end());
                    if(domains[i].empty()) return std::nullopt;
                    changed=changed||domains[i].size()!=old;
                }
            if(changed) break;
        }
    }
    return domains;
}
}
""",
        r"""
int main() {
    using hall_pruner::prune;
    auto a=prune({{1},{1,2},{2,3}}); assert(a && (*a)[1]==std::vector<int>{2} && (*a)[2]==std::vector<int>{3});
    auto b=prune({{1,2},{1,2},{1,2,3}}); assert(b && (*b)[2]==std::vector<int>{3});
    assert(!prune({{1},{1}}));
    assert(prune({}).has_value());
    std::vector<std::vector<int>> too_many(21,{1});
    bool bad=false; try { (void)prune(too_many); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "if(values.size()<variables)",
        "if(values.size()<=variables)",
        "hall-set-pruning",
        ("all-different", "hall-subset", "domain-pruning"),
    ),
    TaskSpec(
        "watched-clue-propagation",
        r"""
namespace watched_clues {
std::optional<std::vector<int>> propagate(
    int variables,const std::vector<Clause>& clauses,std::vector<int> assignment) {
    if(variables<0 || assignment.size()!=static_cast<std::size_t>(variables))
        throw std::invalid_argument("variables");
    for(const auto& clause:clauses) for(const auto& literal:clause.literals)
        if(literal.variable<0||literal.variable>=variables) throw std::invalid_argument("literal");
    bool changed=true;
    while(changed) {
        changed=false;
        for(const auto& clause:clauses) {
            if(clause.literals.empty()) return std::nullopt;
            bool satisfied=false; std::vector<Literal> unknown;
            for(const auto literal:clause.literals) {
                const int value=assignment[static_cast<std::size_t>(literal.variable)];
                if(value<0) unknown.push_back(literal);
                else if((value==literal.value)==literal.equal) satisfied=true;
            }
            if(satisfied) continue;
            if(unknown.empty()) return std::nullopt;
            if(unknown.size()==1 && unknown[0].equal) {
                auto& value=assignment[static_cast<std::size_t>(unknown[0].variable)];
                if(value>=0 && value!=unknown[0].value) return std::nullopt;
                if(value<0) { value=unknown[0].value; changed=true; }
            }
        }
    }
    return assignment;
}
}
""",
        r"""
int main() {
    using namespace watched_clues;
    auto a=propagate(2,{{{{0,1,true}}}}, {-1,-1});
    assert(a && (*a)[0]==1);
    auto b=propagate(2,{{{{0,1,false},{1,2,true}}}}, {1,-1});
    assert(b && (*b)[1]==2);
    auto c=propagate(1,{{{{0,1,true},{0,2,true}}}}, {2}); assert(c);
    assert(!propagate(1,{{}}, {-1}));
    assert(!propagate(1,{{{{0,1,true}}}}, {2}));
    bool bad=false; try { (void)propagate(1,{{{{2,1,true}}}}, {-1}); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "if(unknown.size()==1 && unknown[0].equal)",
        "if(unknown.size()==2 && unknown[0].equal)",
        "watched-clause-propagation",
        ("unit-propagation", "finite-domain-literal", "contradiction"),
    ),
    TaskSpec(
        "exact-cover-dlx",
        r"""
namespace exact_cover {
std::optional<std::vector<int>> lexicographic_solution(
    const std::vector<std::vector<int>>& rows,int columns) {
    if(columns<0) throw std::invalid_argument("columns");
    std::vector<std::vector<int>> normalized=rows;
    for(auto& row:normalized) {
        std::sort(row.begin(),row.end());
        if(std::adjacent_find(row.begin(),row.end())!=row.end()) throw std::invalid_argument("duplicate");
        if(std::any_of(row.begin(),row.end(),[&](int column){return column<0||column>=columns;}))
            throw std::invalid_argument("column");
    }
    std::vector<int> chosen,best; std::vector<bool> covered(static_cast<std::size_t>(columns),false);
    std::function<void()> search=[&]() {
        int first=-1; for(int c=0;c<columns;++c) if(!covered[static_cast<std::size_t>(c)]) {first=c;break;}
        if(first<0) { if(best.empty()||chosen<best) best=chosen; return; }
        for(std::size_t i=0;i<normalized.size();++i) {
            if(std::find(normalized[i].begin(),normalized[i].end(),first)==normalized[i].end()) continue;
            bool overlap=false; for(int c:normalized[i]) overlap=overlap||covered[static_cast<std::size_t>(c)];
            if(overlap) continue;
            for(int c:normalized[i]) covered[static_cast<std::size_t>(c)]=true;
            chosen.push_back(static_cast<int>(i)); search(); chosen.pop_back();
            for(int c:normalized[i]) covered[static_cast<std::size_t>(c)]=false;
        }
    };
    search();
    if(columns==0) return std::vector<int>{};
    if(best.empty()) return std::nullopt;
    return best;
}
}
""",
        r"""
int main() {
    using exact_cover::lexicographic_solution;
    assert((lexicographic_solution({},0)==std::vector<int>{}));
    auto a=lexicographic_solution({{0},{1},{0,1}},2); assert((a && *a==std::vector<int>{0,1}));
    auto b=lexicographic_solution({{0,2},{1},{0},{1,2}},3); assert((b && *b==std::vector<int>{0,1}));
    assert(!lexicographic_solution({{0}},2));
    bool bad=false; try { (void)lexicographic_solution({{0,0}},1); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "if(best.empty()||chosen<best)",
        "if(best.empty()||chosen>best)",
        "exact-cover-search",
        ("exact-cover", "cover-uncover", "lexicographic-solution"),
    ),
    TaskSpec(
        "clue-entailment-check",
        r"""
namespace clue_entailment {
static bool holds(const std::vector<int>& position,Constraint constraint) {
    if(constraint.left<0||constraint.right<0||
       constraint.left>=static_cast<int>(position.size())||
       constraint.right>=static_cast<int>(position.size())||
       constraint.relation<-1||constraint.relation>1) throw std::invalid_argument("constraint");
    const int comparison=position[static_cast<std::size_t>(constraint.left)]<
                         position[static_cast<std::size_t>(constraint.right)]?-1:
                         position[static_cast<std::size_t>(constraint.left)]>
                         position[static_cast<std::size_t>(constraint.right)]?1:0;
    return comparison==constraint.relation;
}
Verdict check(int entities,const std::vector<Constraint>& base,Constraint query) {
    if(entities<0||entities>10) throw std::invalid_argument("entities");
    std::vector<int> permutation(static_cast<std::size_t>(entities));
    std::iota(permutation.begin(),permutation.end(),0);
    bool any=false,truth=false,falsehood=false;
    do {
        std::vector<int> position(static_cast<std::size_t>(entities));
        for(int i=0;i<entities;++i) position[static_cast<std::size_t>(permutation[static_cast<std::size_t>(i)])]=i;
        bool valid=true; for(const auto constraint:base) valid=valid&&holds(position,constraint);
        if(valid) { any=true; (holds(position,query)?truth:falsehood)=true; }
    } while(std::next_permutation(permutation.begin(),permutation.end()));
    if(!any) throw std::domain_error("inconsistent");
    if(truth&&!falsehood) return Verdict::entailed;
    if(falsehood&&!truth) return Verdict::contradicted;
    return Verdict::undecided;
}
}
""",
        r"""
int main() {
    using namespace clue_entailment;
    assert(check(3,{{0,1,-1},{1,2,-1}},{0,2,-1})==Verdict::entailed);
    assert(check(3,{{0,1,-1}},{0,1,1})==Verdict::contradicted);
    assert(check(3,{}, {0,1,-1})==Verdict::undecided);
    assert(check(1,{}, {0,0,0})==Verdict::entailed);
    bool bad=false; try { (void)check(2,{{0,1,-1},{0,1,1}},{0,1,-1}); } catch(const std::domain_error&) { bad=true; }
    assert(bad);
}
""",
        "if(truth&&!falsehood)",
        "if(truth&&falsehood)",
        "clue-entailment",
        ("permutation-models", "universal-query", "three-verdict"),
    ),
    TaskSpec(
        "minimal-unique-clue-set",
        r"""
namespace minimal_clues {
std::vector<std::size_t> select(
    int entities,const std::vector<std::vector<int>>& masks) {
    if(entities<0||entities>63) throw std::invalid_argument("entities");
    std::vector<std::uint64_t> encoded;
    for(const auto& mask:masks) {
        std::uint64_t bits=0;
        for(int value:mask) {
            if(value<0||value>=entities) throw std::invalid_argument("mask");
            bits|=std::uint64_t{1}<<value;
        }
        encoded.push_back(bits);
    }
    const std::uint64_t all=entities==64?~std::uint64_t{0}:
        (entities==0?0:(std::uint64_t{1}<<entities)-1);
    std::vector<std::size_t> best,current;
    std::function<void(std::size_t,std::uint64_t)> search=[&](std::size_t index,std::uint64_t candidates) {
        if(candidates && (candidates&(candidates-1))==0) {
            if(best.empty()||current.size()<best.size()||(current.size()==best.size()&&current<best)) best=current;
            return;
        }
        if(index==encoded.size()||(!best.empty()&&current.size()>=best.size())) return;
        current.push_back(index); search(index+1,candidates&encoded[index]); current.pop_back();
        search(index+1,candidates);
    };
    search(0,all);
    return best;
}
}
""",
        r"""
int main() {
    using minimal_clues::select;
    assert(select(1,{})==std::vector<std::size_t>{});
    assert((select(3,{{0,1},{1,2}})==std::vector<std::size_t>{0,1}));
    assert((select(3,{{0},{1},{2}})==std::vector<std::size_t>{0}));
    assert(select(3,{{0,1,2}}).empty());
    bool bad=false; try { (void)select(2,{{2}}); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "(candidates&(candidates-1))==0",
        "(candidates&(candidates-1))!=0",
        "minimal-clue-subset",
        ("mask-intersection", "branch-and-bound", "unique-candidate"),
    ),
    TaskSpec(
        "soft-clue-maxsat",
        r"""
namespace soft_clues {
Result maximize(int assignment_count,const std::vector<Soft>& clues) {
    if(assignment_count<=0||assignment_count>64) throw std::invalid_argument("assignments");
    for(const auto clue:clues) if(clue.weight<0) throw std::invalid_argument("weight");
    Result best{0,std::numeric_limits<std::int64_t>::min()};
    for(int assignment=0;assignment<assignment_count;++assignment) {
        std::int64_t score=0;
        for(const auto clue:clues) if(clue.satisfying_assignments&(std::uint64_t{1}<<assignment)) {
            if(score>std::numeric_limits<std::int64_t>::max()-clue.weight) throw std::overflow_error("score");
            score+=clue.weight;
        }
        if(score>best.score) best={assignment,score};
    }
    return best;
}
}
""",
        r"""
int main() {
    using soft_clues::Soft; using soft_clues::maximize;
    auto a=maximize(3,{{0b011,2},{0b110,3}}); assert(a.assignment==1&&a.score==5);
    auto b=maximize(3,{}); assert(b.assignment==0&&b.score==0);
    auto c=maximize(2,{{0b11,4}}); assert(c.assignment==0);
    bool bad=false; try { (void)maximize(0,{}); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
    bad=false; try { (void)maximize(2,{{1,-1}}); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "if(score>best.score)",
        "if(score>=best.score)",
        "weighted-maxsat-mask",
        ("soft-clue", "weighted-score", "tie-break"),
    ),
    TaskSpec(
        "symmetry-orbit-canonicalizer",
        r"""
namespace symmetry_orbit {
std::vector<int> canonical(
    std::vector<int> assignment,const std::vector<std::vector<int>>& generators) {
    for(const auto& generator:generators) {
        if(generator.size()!=assignment.size()) throw std::invalid_argument("generator");
        auto sorted=generator; std::sort(sorted.begin(),sorted.end());
        for(std::size_t i=0;i<sorted.size();++i) if(sorted[i]!=static_cast<int>(i))
            throw std::invalid_argument("permutation");
    }
    std::set<std::vector<int>> visited{assignment};
    std::queue<std::vector<int>> queue; queue.push(assignment);
    auto best=assignment;
    while(!queue.empty()) {
        auto current=queue.front(); queue.pop(); best=std::min(best,current);
        for(const auto& generator:generators) {
            std::vector<int> next(current.size());
            for(std::size_t i=0;i<current.size();++i)
                next[i]=current[static_cast<std::size_t>(generator[i])];
            if(visited.insert(next).second) queue.push(std::move(next));
        }
    }
    return best;
}
}
""",
        r"""
int main() {
    using symmetry_orbit::canonical;
    assert((canonical({3,1,2},{{1,0,2}})==std::vector<int>{1,3,2}));
    assert((canonical({2,1},{{0,1}})==std::vector<int>{2,1}));
    assert(canonical({},{}).empty());
    auto a=canonical({3,2,1},{{1,2,0}}); assert(a==std::vector<int>({1,3,2}));
    bool bad=false; try { (void)canonical({1,2},{{0,0}}); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "best=std::min(best,current);",
        "best=std::max(best,current);",
        "symmetry-orbit",
        ("permutation-generator", "orbit-bfs", "canonical-assignment"),
    ),
    TaskSpec(
        "rollback-constraint-session",
        r"""
namespace rollback_csp {
std::vector<std::size_t> domain_sizes(
    int variables,int values,const std::vector<Command>& commands) {
    if(variables<0||values<=0) throw std::invalid_argument("dimensions");
    std::vector<std::set<int>> domains(static_cast<std::size_t>(variables));
    for(auto& domain:domains) for(int value=0;value<values;++value) domain.insert(value);
    std::vector<std::vector<std::set<int>>> checkpoints;
    std::vector<std::size_t> out;
    for(const auto command:commands) {
        if(command.kind==2) checkpoints.push_back(domains);
        else if(command.kind==3) {
            if(checkpoints.empty()) throw std::logic_error("rollback");
            domains=checkpoints.back(); checkpoints.pop_back();
        } else {
            if(command.variable<0||command.variable>=variables||command.value<0||command.value>=values)
                throw std::invalid_argument("command");
            auto candidate=domains;
            auto& domain=candidate[static_cast<std::size_t>(command.variable)];
            if(command.kind==0) {
                if(domain.count(command.value)) domain={command.value};
            } else if(command.kind==1) {
                if(domain.size()>1) domain.erase(command.value);
            } else throw std::invalid_argument("kind");
            if(!domain.empty()) domains=std::move(candidate);
        }
        std::size_t total=0; for(const auto& domain:domains) total+=domain.size();
        out.push_back(total);
    }
    return out;
}
}
""",
        r"""
int main() {
    using rollback_csp::Command; using rollback_csp::domain_sizes;
    assert((domain_sizes(2,3,{{0,0,1}})==std::vector<std::size_t>{4}));
    assert((domain_sizes(1,2,{{1,0,0},{1,0,1}})==std::vector<std::size_t>{1,1}));
    auto a=domain_sizes(1,3,{{2,0,0},{1,0,0},{2,0,0},{1,0,1},{3,0,0},{3,0,0}});
    assert((a==std::vector<std::size_t>{3,2,2,1,2,3}));
    bool bad=false; try { (void)domain_sizes(1,2,{{3,0,0}}); } catch(const std::logic_error&) { bad=true; }
    assert(bad);
}
""",
        "if(!domain.empty()) domains=std::move(candidate);",
        "if(domain.empty()) domains=std::move(candidate);",
        "rollback-domains",
        ("checkpoint", "change-log", "transactional-reject"),
    ),
    TaskSpec(
        "nogood-learning-search",
        r"""
namespace nogood_search {
std::optional<std::vector<int>> solve(
    int variables,int values,const std::vector<BinaryBan>& bans) {
    if(variables<0||values<=0) throw std::invalid_argument("dimensions");
    for(const auto ban:bans)
        if(ban.a_var<0||ban.b_var<0||ban.a_var>=variables||ban.b_var>=variables||
           ban.a_val<0||ban.b_val<0||ban.a_val>=values||ban.b_val>=values)
            throw std::invalid_argument("ban");
    std::vector<int> assignment(static_cast<std::size_t>(variables),-1);
    std::set<std::vector<int>> nogoods;
    std::function<bool(int)> search=[&](int variable) {
        if(variable==variables) return true;
        if(nogoods.count(assignment)) return false;
        for(int value=0;value<values;++value) {
            assignment[static_cast<std::size_t>(variable)]=value;
            bool valid=true;
            for(const auto ban:bans) {
                const int av=assignment[static_cast<std::size_t>(ban.a_var)];
                const int bv=assignment[static_cast<std::size_t>(ban.b_var)];
                if(av==ban.a_val&&bv==ban.b_val) {valid=false;break;}
            }
            if(valid&&search(variable+1)) return true;
        }
        assignment[static_cast<std::size_t>(variable)]=-1;
        nogoods.insert(assignment);
        return false;
    };
    if(!search(0)) return std::nullopt;
    return assignment;
}
}
""",
        r"""
int main() {
    using nogood_search::BinaryBan; using nogood_search::solve;
    auto a=solve(2,2,{{0,0,1,0}}); assert(a&&*a==std::vector<int>({0,1}));
    assert(!solve(1,1,{{0,0,0,0}}));
    auto b=solve(3,2,{{0,0,1,0},{1,0,2,0}}); assert(b&&b->size()==3);
    auto c=solve(0,2,{}); assert(c&&c->empty());
    bool bad=false; try { (void)solve(1,2,{{0,2,0,1}}); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "for(int value=0;value<values;++value)",
        "for(int value=values-1;value>=0;--value)",
        "nogood-search",
        ("forward-check", "learned-nogood", "lexicographic-assignment"),
    ),
    TaskSpec(
        "explanation-dag",
        r"""
namespace explanation_dag {
std::vector<int> shortest_explanation(
    int facts,const std::vector<int>& given,const std::vector<Implication>& rules,int target) {
    if(facts<0||target<0||target>=facts) throw std::invalid_argument("facts");
    std::vector<std::vector<int>> graph(static_cast<std::size_t>(facts));
    for(const auto rule:rules) {
        if(rule.premise<0||rule.conclusion<0||rule.premise>=facts||rule.conclusion>=facts)
            throw std::invalid_argument("rule");
        graph[static_cast<std::size_t>(rule.premise)].push_back(rule.conclusion);
    }
    std::vector<int> sorted=given; std::sort(sorted.begin(),sorted.end());
    sorted.erase(std::unique(sorted.begin(),sorted.end()),sorted.end());
    for(int source:sorted) {
        if(source<0||source>=facts) throw std::invalid_argument("given");
        std::vector<bool> seen(static_cast<std::size_t>(facts),false);
        std::queue<int> queue; queue.push(source); seen[static_cast<std::size_t>(source)]=true;
        while(!queue.empty()) {
            const int fact=queue.front(); queue.pop();
            if(fact==target) return {source};
            for(int next:graph[static_cast<std::size_t>(fact)])
                if(!seen[static_cast<std::size_t>(next)]) {
                    seen[static_cast<std::size_t>(next)]=true; queue.push(next);
                }
        }
    }
    return {};
}
}
""",
        r"""
int main() {
    using explanation_dag::Implication; using explanation_dag::shortest_explanation;
    assert((shortest_explanation(4,{0,1},{{0,2},{2,3}},3)==std::vector<int>{0}));
    assert((shortest_explanation(3,{2,1},{},1)==std::vector<int>{1}));
    assert(shortest_explanation(3,{0},{{0,1},{1,0}},2).empty());
    assert((shortest_explanation(3,{2,0},{{2,1},{0,1}},1)==std::vector<int>{0}));
    bool bad=false; try { (void)shortest_explanation(2,{0},{{0,2}},1); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "if(fact==target) return {source};",
        "if(fact==target) return {target};",
        "explanation-reachability",
        ("implication-dag", "smallest-given", "cycle-safe"),
    ),
    TaskSpec(
        "treewidth-clue-count",
        r"""
namespace clue_tree_dp {
std::uint64_t count(int variables,int values,const std::vector<EdgeRule>& forest) {
    if(variables<0||values<=0) throw std::invalid_argument("dimensions");
    using Edge=std::pair<int,std::set<std::pair<int,int>>>;
    std::vector<std::vector<Edge>> graph(static_cast<std::size_t>(variables));
    for(const auto& edge:forest) {
        if(edge.parent<0||edge.child<0||edge.parent>=variables||edge.child>=variables||
           edge.parent==edge.child) throw std::invalid_argument("edge");
        std::set<std::pair<int,int>> allowed(edge.allowed.begin(),edge.allowed.end()),reverse;
        for(const auto& pair:allowed) {
            if(pair.first<0||pair.second<0||pair.first>=values||pair.second>=values)
                throw std::invalid_argument("value");
            reverse.insert({pair.second,pair.first});
        }
        graph[static_cast<std::size_t>(edge.parent)].push_back({edge.child,allowed});
        graph[static_cast<std::size_t>(edge.child)].push_back({edge.parent,reverse});
    }
    std::vector<int> parent(static_cast<std::size_t>(variables),-2),order;
    std::vector<std::vector<std::uint64_t>> dp(static_cast<std::size_t>(variables),
                                               std::vector<std::uint64_t>(static_cast<std::size_t>(values),1));
    std::uint64_t total=1;
    for(int root=0;root<variables;++root) if(parent[static_cast<std::size_t>(root)]==-2) {
        parent[static_cast<std::size_t>(root)]=-1; order.clear(); std::queue<int> queue; queue.push(root);
        while(!queue.empty()) {
            int node=queue.front(); queue.pop(); order.push_back(node);
            for(const auto& [next,allowed]:graph[static_cast<std::size_t>(node)]) {
                (void)allowed;
                if(parent[static_cast<std::size_t>(next)]==-2) {
                    parent[static_cast<std::size_t>(next)]=node; queue.push(next);
                } else if(parent[static_cast<std::size_t>(node)]!=next) throw std::invalid_argument("cycle");
            }
        }
        for(auto it=order.rbegin();it!=order.rend();++it) {
            const int node=*it;
            for(const auto& [child,allowed]:graph[static_cast<std::size_t>(node)])
                if(parent[static_cast<std::size_t>(child)]==node) {
                    for(int value=0;value<values;++value) {
                        std::uint64_t sum=0;
                        for(int cv=0;cv<values;++cv) if(allowed.count({value,cv})) {
                            if(sum>std::numeric_limits<std::uint64_t>::max()-dp[static_cast<std::size_t>(child)][static_cast<std::size_t>(cv)])
                                throw std::overflow_error("count");
                            sum+=dp[static_cast<std::size_t>(child)][static_cast<std::size_t>(cv)];
                        }
                        auto& here=dp[static_cast<std::size_t>(node)][static_cast<std::size_t>(value)];
                        if(sum && here>std::numeric_limits<std::uint64_t>::max()/sum) throw std::overflow_error("count");
                        here*=sum;
                    }
                }
        }
        std::uint64_t component=0;
        for(auto value:dp[static_cast<std::size_t>(root)]) {
            if(component>std::numeric_limits<std::uint64_t>::max()-value) throw std::overflow_error("count");
            component+=value;
        }
        if(component && total>std::numeric_limits<std::uint64_t>::max()/component) throw std::overflow_error("count");
        total*=component;
    }
    return total;
}
}
""",
        r"""
int main() {
    using clue_tree_dp::count;
    assert(count(1,3,{})==3);
    assert(count(2,2,{{0,1,{{0,1},{1,0}}}})==2);
    assert(count(3,2,{{0,1,{{0,0},{1,1}}},{1,2,{{0,0},{1,1}}}})==2);
    assert(count(0,2,{})==1);
    bool bad=false; try { (void)count(3,2,{{0,1,{}},{1,2,{}},{2,0,{}}}); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "here*=sum;",
        "here+=sum;",
        "forest-clue-dp",
        ("tree-dp", "allowed-pairs", "checked-count"),
    ),
    TaskSpec(
        "kth-lexicographic-solution",
        r"""
namespace kth_solution {
std::optional<std::vector<int>> kth(
    int variables,int values,const std::vector<Ban>& bans,std::uint64_t index) {
    if(variables<0||values<0||variables>values||values>63) return std::nullopt;
    std::vector<std::uint64_t> forbidden(static_cast<std::size_t>(variables),0);
    for(const auto ban:bans) {
        if(ban.variable<0||ban.variable>=variables||ban.value<0||ban.value>=values)
            throw std::invalid_argument("ban");
        forbidden[static_cast<std::size_t>(ban.variable)]|=std::uint64_t{1}<<ban.value;
    }
    std::map<std::pair<int,std::uint64_t>,std::uint64_t> memo;
    std::function<std::uint64_t(int,std::uint64_t)> ways=[&](int variable,std::uint64_t used) {
        if(variable==variables) return std::uint64_t{1};
        auto key=std::make_pair(variable,used); auto found=memo.find(key); if(found!=memo.end()) return found->second;
        std::uint64_t total=0;
        for(int value=0;value<values;++value) if(!(used&(std::uint64_t{1}<<value))&&
            !(forbidden[static_cast<std::size_t>(variable)]&(std::uint64_t{1}<<value))) {
            const auto add=ways(variable+1,used|(std::uint64_t{1}<<value));
            total=std::numeric_limits<std::uint64_t>::max()-total<add?
                std::numeric_limits<std::uint64_t>::max():total+add;
        }
        return memo[key]=total;
    };
    if(index>=ways(0,0)) return std::nullopt;
    std::vector<int> answer; std::uint64_t used=0;
    for(int variable=0;variable<variables;++variable) for(int value=0;value<values;++value)
        if(!(used&(std::uint64_t{1}<<value))&&
           !(forbidden[static_cast<std::size_t>(variable)]&(std::uint64_t{1}<<value))) {
            const auto count=ways(variable+1,used|(std::uint64_t{1}<<value));
            if(index>=count) index-=count;
            else {answer.push_back(value);used|=std::uint64_t{1}<<value;break;}
        }
    return answer;
}
}
""",
        r"""
int main() {
    using kth_solution::kth;
    assert(kth(2,3,{},0)==std::vector<int>({0,1}));
    assert(kth(2,3,{},1)==std::vector<int>({0,2}));
    assert(kth(2,3,{{0,0}},0)==std::vector<int>({1,0}));
    assert(!kth(4,3,{},0));
    assert(!kth(2,2,{},2));
    assert(kth(0,0,{},0)==std::vector<int>{});
}
""",
        "if(index>=count) index-=count;",
        "if(index>count) index-=count;",
        "injective-unranking",
        ("subset-dp", "lexicographic-unrank", "saturated-count"),
    ),
    TaskSpec(
        "weighted-clue-diagnosis",
        r"""
namespace clue_diagnosis {
std::vector<std::size_t> remove_for_consistency(
    int assignments,const std::vector<Clue>& clues) {
    if(assignments<=0||assignments>64) throw std::invalid_argument("assignments");
    for(const auto clue:clues) if(clue.removal_cost<0) throw std::invalid_argument("cost");
    const std::uint64_t all=assignments==64?~std::uint64_t{0}:(std::uint64_t{1}<<assignments)-1;
    std::vector<std::size_t> best,current; std::int64_t best_cost=std::numeric_limits<std::int64_t>::max();
    std::function<void(std::size_t,std::uint64_t,std::int64_t)> search=
        [&](std::size_t index,std::uint64_t candidates,std::int64_t cost) {
            if(cost>best_cost) return;
            if(index==clues.size()) {
                if(candidates&&(cost<best_cost||(cost==best_cost&&(best.empty()||current<best)))) {
                    best_cost=cost; best=current;
                }
                return;
            }
            search(index+1,candidates&clues[index].mask,cost);
            current.push_back(index);
            search(index+1,candidates,cost+clues[index].removal_cost);
            current.pop_back();
        };
    search(0,all,0);
    return best;
}
}
""",
        r"""
int main() {
    using clue_diagnosis::remove_for_consistency;
    assert(remove_for_consistency(3,{{0b111,5}}).empty());
    assert((remove_for_consistency(2,{{0b01,2},{0b10,3}})==std::vector<std::size_t>{0}));
    assert((remove_for_consistency(2,{{0b01,1},{0b10,1}})==std::vector<std::size_t>{0}));
    auto a=remove_for_consistency(3,{{0b001,2},{0b010,2},{0b100,9}}); assert(!a.empty());
    bool bad=false; try { (void)remove_for_consistency(0,{}); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "if(cost>best_cost)",
        "if(cost>=best_cost)",
        "weighted-diagnosis",
        ("minimum-removal", "candidate-mask", "lexicographic-set"),
    ),
    TaskSpec(
        "constraint-order-optimizer",
        r"""
namespace clue_order {
static int bit_count(std::uint64_t value) {
    int count=0;
    while(value) { value&=value-1; ++count; }
    return count;
}
std::vector<std::size_t> greedy_order(
    std::uint64_t candidates,const std::vector<std::uint64_t>& masks) {
    if(candidates==0) throw std::invalid_argument("candidates");
    std::vector<bool> used(masks.size(),false); std::vector<std::size_t> out;
    while(true) {
        std::optional<std::size_t> best; int elimination=0;
        for(std::size_t i=0;i<masks.size();++i) if(!used[i]) {
            const auto next=candidates&masks[i];
            const int removed=bit_count(candidates)-bit_count(next);
            if(removed>elimination) {elimination=removed;best=i;}
        }
        if(!best) break;
        used[*best]=true; out.push_back(*best); candidates&=masks[*best];
    }
    return out;
}
}
""",
        r"""
int main() {
    using clue_order::greedy_order;
    assert((greedy_order(0b1111,{0b0011,0b0101})==std::vector<std::size_t>{0,1}));
    assert(greedy_order(0b11,{0b11,0b11}).empty());
    assert((greedy_order(0b111,{0b011,0b001})==std::vector<std::size_t>{1}));
    auto a=greedy_order(0b1111,{0b0111,0b1011,0b1101}); assert(a[0]==0);
    bool bad=false; try { (void)greedy_order(0,{}); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "if(removed>elimination)",
        "if(removed>=elimination)",
        "greedy-clue-order",
        ("marginal-elimination", "candidate-bitset", "redundancy-stop"),
    ),
)

BY_SLUG = {spec.slug: spec for spec in SPECS}
if len(BY_SLUG) != 15:
    raise ValueError("Zebra Puzzle owner must define exactly 15 unique tasks")
