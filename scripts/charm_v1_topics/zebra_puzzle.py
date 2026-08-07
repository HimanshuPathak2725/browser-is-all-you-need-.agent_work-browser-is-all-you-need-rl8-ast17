"""Owner source for the three CHARM V1 Zebra Puzzle tasks."""

from __future__ import annotations

from scripts.charm_v1_topics.common import package, prompt, support


ENGINE = r'''#pragma once
#include <algorithm>
#include <cmath>
#include <functional>
#include <map>
#include <optional>
#include <set>
#include <string>
#include <vector>
namespace charm::zebra {
enum class ClueKind { same_house, adjacent, immediately_left };
struct Clue { ClueKind kind; std::string a; std::string b; };
inline bool clues_hold(const std::map<std::string,int>& assignment, const std::vector<Clue>& clues) {
    for (const Clue& clue : clues) {
        const auto a=assignment.find(clue.a), b=assignment.find(clue.b);
        if(a==assignment.end()||b==assignment.end())return false;
        if(clue.kind==ClueKind::same_house && a->second!=b->second)return false;
        if(clue.kind==ClueKind::adjacent && std::abs(a->second-b->second)!=1)return false;
        if(clue.kind==ClueKind::immediately_left && a->second+1!=b->second)return false;
    }
    return true;
}
inline bool partial_clues_hold(const std::map<std::string,int>& assignment, const std::set<std::string>& assigned, const std::vector<Clue>& clues) {
    for (const Clue& clue : clues) {
        if (assigned.count(clue.a) == 0U || assigned.count(clue.b) == 0U) continue;
        const int a = assignment.at(clue.a), b = assignment.at(clue.b);
        if (clue.kind == ClueKind::same_house && a != b) return false;
        if (clue.kind == ClueKind::adjacent && std::abs(a - b) != 1) return false;
        if (clue.kind == ClueKind::immediately_left && a + 1 != b) return false;
    }
    return true;
}
inline std::optional<std::map<std::string,int>> solve_unique(int houses, const std::vector<std::vector<std::string>>& categories, const std::vector<Clue>& clues) {
    if(houses<=0||categories.empty())return std::nullopt;
    std::set<std::string> items;
    for(const auto& category:categories){if(category.size()!=static_cast<std::size_t>(houses))return std::nullopt;for(const auto& item:category)if(item.empty()||!items.insert(item).second)return std::nullopt;}
    for(const auto& clue:clues)if(items.count(clue.a)==0U||items.count(clue.b)==0U)return std::nullopt;
    std::map<std::string,int> current, solution; std::set<std::string> assigned; int count=0;
    std::function<void(std::size_t)> search=[&](std::size_t category_index){
        if(count>1)return;
        if(category_index==categories.size()){if(clues_hold(current,clues)){solution=current;++count;}return;}
        std::vector<int> order(static_cast<std::size_t>(houses)); for(int i=0;i<houses;++i)order[static_cast<std::size_t>(i)]=i;
        do {
            for(int i=0;i<houses;++i) {
                const std::string& item = categories[category_index][static_cast<std::size_t>(i)];
                current[item]=order[static_cast<std::size_t>(i)];
                assigned.insert(item);
            }
            if (partial_clues_hold(current, assigned, clues)) search(category_index+1);
            for (const std::string& item : categories[category_index]) assigned.erase(item);
        } while(std::next_permutation(order.begin(),order.end()));
    };
    search(0); return count==1?std::optional<std::map<std::string,int>>(solution):std::nullopt;
}
}
'''
ENGINE_TEST = r'''#include "house-constraint-engine.h"
#include <cassert>
using charm::zebra::Clue;
using charm::zebra::ClueKind;
using charm::zebra::solve_unique;
int main() {
    assert(!solve_unique(0,{{"a"}},{}));
    assert(!solve_unique(2,{{"a"}},{}));
    assert(!solve_unique(2,{{"a","a"}},{}));
    const std::vector<std::vector<std::string>> categories{{"Ada","Bob"},{"cat","dog"}};
    assert(!solve_unique(2,categories,{}));
    const auto unique=solve_unique(2,categories,{{ClueKind::same_house,"Ada","dog"},{ClueKind::immediately_left,"Ada","Bob"}});
    assert(unique && unique->at("Ada")==0 && unique->at("dog")==0 && unique->at("Bob")==1);
    assert(!solve_unique(2,categories,{{ClueKind::same_house,"Ada","dog"},{ClueKind::same_house,"Ada","cat"}}));
    assert(!solve_unique(2,categories,{{ClueKind::same_house,"missing","cat"}}));
    const auto adjacent=solve_unique(2,categories,{{ClueKind::same_house,"Ada","cat"},{ClueKind::immediately_left,"cat","dog"}});
    assert(adjacent && adjacent->at("dog")==1);
    return 0;
}
'''


VERIFY = r'''#include <cmath>
#include <map>
#include <set>
#include <string>
#include <vector>
namespace charm::zebra {
enum class ClueKind { same_house, adjacent, immediately_left };
struct Clue { ClueKind kind; std::string a; std::string b; };
struct Verification { bool complete; std::vector<std::size_t> violated; };
inline Verification verify(int houses, const std::vector<std::vector<std::string>>& categories, const std::vector<Clue>& clues, const std::map<std::string,int>& assignment) {
    bool complete=houses>0; std::set<std::string> expected;
    for(const auto& category:categories){if(category.size()!=static_cast<std::size_t>(houses))complete=false;std::set<int> occupied;for(const auto& item:category){expected.insert(item);const auto found=assignment.find(item);if(found==assignment.end()||found->second<0||found->second>=houses||!occupied.insert(found->second).second)complete=false;}}
    if(assignment.size()!=expected.size())complete=false;
    std::vector<std::size_t> violated;
    for(std::size_t index=0;index<clues.size();++index){const auto a=assignment.find(clues[index].a),b=assignment.find(clues[index].b);bool pass=a!=assignment.end()&&b!=assignment.end();if(pass&&clues[index].kind==ClueKind::same_house)pass=a->second==b->second;if(pass&&clues[index].kind==ClueKind::adjacent)pass=std::abs(a->second-b->second)==1;if(pass&&clues[index].kind==ClueKind::immediately_left)pass=a->second+1==b->second;if(!pass)violated.push_back(index);}
    return {complete,violated};
}
}
'''
VERIFY_START = VERIFY.replace("if(!pass)violated.push_back(index);", "if(pass)violated.push_back(index);")
VERIFY_TEST = r'''#include "solution-certificate.cpp"
#include <cassert>
using charm::zebra::ClueKind;
using charm::zebra::verify;
int main() {
    const std::vector<std::vector<std::string>> categories{{"Ada","Bob"},{"cat","dog"}};
    const std::vector<charm::zebra::Clue> clues{{ClueKind::same_house,"Ada","cat"},{ClueKind::immediately_left,"Ada","Bob"},{ClueKind::adjacent,"cat","dog"}};
    const auto good=verify(2,categories,clues,{{"Ada",0},{"Bob",1},{"cat",0},{"dog",1}});
    assert(good.complete && good.violated.empty());
    const auto wrong=verify(2,categories,clues,{{"Ada",1},{"Bob",0},{"cat",0},{"dog",1}});
    assert(wrong.complete && wrong.violated==std::vector<std::size_t>({0,1}));
    const auto missing=verify(2,categories,clues,{{"Ada",0},{"Bob",1},{"cat",0}});
    assert(!missing.complete && missing.violated==std::vector<std::size_t>({2}));
    const auto duplicate=verify(2,categories,clues,{{"Ada",0},{"Bob",0},{"cat",0},{"dog",1}});
    assert(!duplicate.complete);
    const auto extra=verify(2,categories,clues,{{"Ada",0},{"Bob",1},{"cat",0},{"dog",1},{"fox",0}});
    assert(!extra.complete);
    assert(!verify(0,categories,clues,{}).complete);
    return 0;
}
'''


CORE = r'''#pragma once
#include <algorithm>
#include <cmath>
#include <functional>
#include <map>
#include <numeric>
#include <set>
#include <string>
#include <vector>
namespace charm::zebra {
enum class ClueKind { same_house, adjacent, immediately_left };
struct Clue { ClueKind kind; std::string a; std::string b; };
inline bool core_satisfiable(
    int houses,
    const std::vector<std::vector<std::string>>& categories,
    const std::vector<Clue>& clues,
    const std::vector<std::size_t>& selected) {
    if (houses <= 0 || categories.empty()) return false;
    std::set<std::string> items;
    for (const auto& category : categories) {
        if (category.size() != static_cast<std::size_t>(houses)) return false;
        for (const auto& item : category) if (!items.insert(item).second) return false;
    }
    for (std::size_t index : selected)
        if (index >= clues.size() || items.count(clues[index].a) == 0U || items.count(clues[index].b) == 0U) return false;
    std::map<std::string,int> current;
    bool found = false;
    std::function<void(std::size_t)> search = [&](std::size_t category_index) {
        if (found) return;
        if (category_index == categories.size()) {
            for (std::size_t index : selected) {
                const auto& clue = clues[index];
                const int a = current[clue.a];
                const int b = current[clue.b];
                if (clue.kind == ClueKind::same_house && a != b) return;
                if (clue.kind == ClueKind::adjacent && std::abs(a - b) != 1) return;
                if (clue.kind == ClueKind::immediately_left && a + 1 != b) return;
            }
            found = true;
            return;
        }
        std::vector<int> order(static_cast<std::size_t>(houses));
        std::iota(order.begin(), order.end(), 0);
        do {
            for (int house = 0; house < houses; ++house)
                current[categories[category_index][static_cast<std::size_t>(house)]] = order[static_cast<std::size_t>(house)];
            search(category_index + 1);
        } while (std::next_permutation(order.begin(), order.end()));
    };
    search(0);
    return found;
}
inline std::vector<std::size_t> contradiction_core(
    int houses,
    const std::vector<std::vector<std::string>>& categories,
    const std::vector<Clue>& clues) {
    std::vector<std::size_t> core(clues.size());
    std::iota(core.begin(), core.end(), 0);
    if (core_satisfiable(houses, categories, clues, core)) return {};
    for (std::size_t position = 0; position < core.size();) {
        auto candidate = core;
        candidate.erase(candidate.begin() + static_cast<long long>(position));
        if (!core_satisfiable(houses, categories, clues, candidate)) core = std::move(candidate);
        else ++position;
    }
    return core;
}
}
'''
CORE_TEST = r'''#include "contradiction-core-repair.h"
#include <cassert>
using charm::zebra::Clue;
using charm::zebra::ClueKind;
using charm::zebra::contradiction_core;
int main(){
    const std::vector<std::vector<std::string>> categories{{"Ada","Bob"},{"cat","dog"}};
    assert(contradiction_core(2,categories,{}).empty());
    const std::vector<Clue> satisfiable{{ClueKind::same_house,"Ada","cat"}};
    assert(contradiction_core(2,categories,satisfiable).empty());
    const std::vector<Clue> contradictory{{ClueKind::same_house,"Ada","cat"},{ClueKind::same_house,"Ada","dog"},{ClueKind::adjacent,"cat","dog"}};
    const auto core=contradiction_core(2,categories,contradictory);
    assert(core==std::vector<std::size_t>({0,1}));
    const std::vector<Clue> order{{ClueKind::immediately_left,"Ada","Bob"},{ClueKind::immediately_left,"Bob","Ada"}};
    assert(contradiction_core(2,categories,order)==std::vector<std::size_t>({0,1}));
    const auto repeated=contradiction_core(2,categories,contradictory);assert(repeated==core);
    assert(!core.empty());
    return 0;
}
'''


def tasks() -> list[dict]:
    engine=["house-constraint-engine.h","house-constraint-engine.cpp"]
    verify_files=["solution-certificate.cpp"]
    core_files=["contradiction-core-repair.h","contradiction-core-repair.cpp"]
    return [
        package(topic="Zebra Puzzle",task_id="charm-v1-house-constraint-engine",instructions=prompt("House constraint engine","Solve a small category-permutation house puzzle and return an assignment only when exactly one assignment satisfies all equality, adjacency, and immediately-left clues.","namespace charm::zebra { enum class ClueKind { same_house, adjacent, immediately_left }; struct Clue { ClueKind kind; std::string a; std::string b; }; std::optional<std::map<std::string,int>> solve_unique(int,const std::vector<std::vector<std::string>>&,const std::vector<Clue>&); }",["positive house count","each category has exactly one item per house","item names are globally unique","every clue name exists","zero or multiple solutions return nullopt"],engine),editable={engine[0]:"#pragma once\nnamespace charm::zebra {}\n",engine[1]:support(engine[0],161)},reference={engine[0]:ENGINE,engine[1]:support(engine[0],162)},hidden_name="house-constraint-engine_test.cpp",hidden=ENGINE_TEST,category="unique-csp",tags=["runtime-repair","backtracking","constraints","header-extension"]),
        package(topic="Zebra Puzzle",task_id="charm-v1-solution-certificate",instructions=prompt("House solution certificate","Verify category completeness and a proposed item-to-house assignment, returning stable zero-based indices of every violated clue.","namespace charm::zebra { enum class ClueKind { same_house, adjacent, immediately_left }; struct Clue { ClueKind kind; std::string a; std::string b; }; struct Verification { bool complete; std::vector<std::size_t> violated; }; Verification verify(int,const std::vector<std::vector<std::string>>&,const std::vector<Clue>&,const std::map<std::string,int>&); }",["every category item appears once","each category occupies every house once","extra assignment items make complete false","missing clue operands violate that clue","violated indices preserve input order"],verify_files),editable={verify_files[0]:VERIFY_START},reference={verify_files[0]:VERIFY},hidden_name="solution-certificate_test.cpp",hidden=VERIFY_TEST,category="certificate-verification",tags=["semantic-bug","verification","stable-index","cpp-only"]),
        package(topic="Zebra Puzzle",task_id="charm-v1-contradiction-core-repair",instructions=prompt("Contradiction core repair","Return a deterministic inclusion-minimal list of clue indices whose selected clues are unsatisfiable; return empty when all clues are satisfiable.","namespace charm::zebra { enum class ClueKind { same_house, adjacent, immediately_left }; struct Clue { ClueKind kind; std::string a; std::string b; }; std::vector<std::size_t> contradiction_core(int,const std::vector<std::vector<std::string>>&,const std::vector<Clue>&); }",["satisfiable puzzle returns empty","all output indices refer to input clues","the selected set is unsatisfiable","removing any selected clue restores satisfiability","output is deterministic"],core_files),editable={core_files[0]:"#pragma once\nnamespace charm::zebra {}\n",core_files[1]:support(core_files[0],163)},reference={core_files[0]:CORE,core_files[1]:support(core_files[0],164)},hidden_name="contradiction-core-repair_test.cpp",hidden=CORE_TEST,category="minimal-conflict",tags=["boundary","minimal-core","determinism","header-edit"]),
    ]
