"""Owner source for the three CHARM V1 Yacht tasks."""

from __future__ import annotations

from scripts.charm_v1_topics.common import calibration_prompt, package, prompt, support


SCORE = r'''#pragma once
#include <algorithm>
#include <limits>
#include <map>
#include <optional>
#include <vector>
namespace charm::yacht {
enum class RuleKind { exact_group, straight, value_sum };
struct Category { RuleKind kind; int argument; };
inline std::optional<int> score(const std::vector<int>& dice, int sides, Category category) {
    if (dice.size() != 5 || sides < 1) return std::nullopt;
    std::map<int,int> counts;
    for (int die : dice) { if (die < 1 || die > sides) return std::nullopt; ++counts[die]; }
    long long result = 0;
    if (category.kind == RuleKind::value_sum) {
        if (category.argument < 1 || category.argument > sides) return std::nullopt;
        result = static_cast<long long>(category.argument) * counts[category.argument];
    } else if (category.kind == RuleKind::exact_group) {
        if (category.argument < 1 || category.argument > 5) return std::nullopt;
        for (const auto& item : counts) if (item.second == category.argument)
            result = std::max(result, static_cast<long long>(item.first) * item.second);
    } else if (category.kind == RuleKind::straight) {
        if (category.argument < 1 || category.argument > 5) return std::nullopt;
        std::vector<int> unique;
        for (const auto& item : counts) unique.push_back(item.first);
        if (unique.size() != static_cast<std::size_t>(category.argument)) return 0;
        for (std::size_t i = 1; i < unique.size(); ++i) if (unique[i] != unique[i-1] + 1) return 0;
        for (int face : unique) result += face;
    } else return std::nullopt;
    if (result > std::numeric_limits<int>::max()) return std::nullopt;
    return static_cast<int>(result);
}
}
'''
SCORE_TEST = r'''#include "configurable-dice-score.h"
#include <cassert>
#include <limits>
using charm::yacht::Category;
using charm::yacht::RuleKind;
using charm::yacht::score;
int main() {
    assert(!score({1,2}, 6, {RuleKind::value_sum,1}));
    assert(!score({0,1,2,3,4}, 6, {RuleKind::straight,5}));
    assert(score({2,2,2,5,5}, 6, {RuleKind::exact_group,3}) == 6);
    assert(score({2,2,2,5,5}, 6, {RuleKind::exact_group,2}) == 10);
    assert(score({1,2,3,4,5}, 6, {RuleKind::straight,5}) == 15);
    assert(score({1,2,3,4,6}, 6, {RuleKind::straight,5}) == 0);
    assert(score({6,6,1,2,6}, 6, {RuleKind::value_sum,6}) == 18);
    assert(!score({1,2,3,4,5}, 6, {RuleKind::value_sum,7}));
    const int maximum = std::numeric_limits<int>::max();
    assert(!score({maximum,maximum,maximum,maximum,maximum}, maximum, {RuleKind::value_sum,maximum}));
    assert(!score({maximum-4,maximum-3,maximum-2,maximum-1,maximum}, maximum, {RuleKind::straight,5}));
    return 0;
}
'''


ASSIGN = r'''#include <algorithm>
#include <limits>
#include <map>
#include <optional>
#include <utility>
#include <vector>
namespace charm::yacht {
enum class RuleKind { exact_group, straight, value_sum };
struct Category { RuleKind kind; int argument; };
struct Assignment { int total; std::vector<std::size_t> categories; };
static std::optional<int> assignment_score(
    const std::vector<int>& dice, int sides, Category category) {
    if (dice.size() != 5 || sides < 1) return std::nullopt;
    std::map<int, int> counts;
    for (int die : dice) {
        if (die < 1 || die > sides) return std::nullopt;
        ++counts[die];
    }
    long long result = 0;
    if (category.kind == RuleKind::value_sum) {
        if (category.argument < 1 || category.argument > sides) return std::nullopt;
        result = static_cast<long long>(category.argument) * counts[category.argument];
    } else if (category.kind == RuleKind::exact_group) {
        if (category.argument < 1 || category.argument > 5) return std::nullopt;
        for (const auto& item : counts) {
            if (item.second == category.argument)
                result = std::max(
                    result, static_cast<long long>(item.first) * item.second);
        }
    } else {
        if (category.argument < 1 || category.argument > 5) return std::nullopt;
        std::vector<int> unique;
        for (const auto& item : counts) unique.push_back(item.first);
        if (unique.size() != static_cast<std::size_t>(category.argument)) return 0;
        for (std::size_t index = 1; index < unique.size(); ++index)
            if (unique[index] != unique[index - 1] + 1) return 0;
        for (int face : unique) result += face;
    }
    if (result > std::numeric_limits<int>::max()) return std::nullopt;
    return static_cast<int>(result);
}
inline std::optional<Assignment> optimize(
    const std::vector<std::vector<int>>& rolls,
    const std::vector<Category>& categories,
    int sides) {
    if (rolls.size() > categories.size()) return std::nullopt;
    if (rolls.empty()) return Assignment{0, {}};
    if (categories.size() > std::numeric_limits<std::size_t>::digits)
        return std::nullopt;
    std::map<std::size_t, Assignment> states;
    states.emplace(0U, Assignment{0, {}});
    for (const auto& roll : rolls) {
        std::map<std::size_t, Assignment> next;
        for (const auto& state : states) {
            for (std::size_t category = 0; category < categories.size(); ++category) {
                const std::size_t bit = std::size_t{1} << category;
                if ((state.first & bit) != 0U) continue;
                const auto value = assignment_score(roll, sides, categories[category]);
                if (!value ||
                    state.second.total > std::numeric_limits<int>::max() - *value) {
                    continue;
                }
                Assignment candidate = state.second;
                candidate.total += *value;
                candidate.categories.push_back(category);
                const std::size_t mask = state.first | bit;
                const auto current = next.find(mask);
                if (current == next.end() ||
                    candidate.total > current->second.total ||
                    (candidate.total == current->second.total &&
                     candidate.categories < current->second.categories)) {
                    next[mask] = std::move(candidate);
                }
            }
        }
        if (next.empty()) return std::nullopt;
        states = std::move(next);
    }
    Assignment best{-1, {}};
    for (const auto& state : states) {
        if (state.second.total > best.total ||
            (state.second.total == best.total &&
             state.second.categories < best.categories)) {
            best = state.second;
        }
    }
    return best;
}
}
'''
ASSIGN_TEST = r'''#include "scorecard-assignment.cpp"
#include <cassert>
#include <vector>
using charm::yacht::Category;
using charm::yacht::RuleKind;
using charm::yacht::optimize;
int main() {
    const std::vector<Category> categories{{RuleKind::value_sum,1},{RuleKind::value_sum,6},{RuleKind::exact_group,3}};
    const auto empty=optimize({},categories,6); assert(empty && empty->total==0 && empty->categories.empty());
    assert(!optimize({{1,1,1,1,1},{2,2,2,2,2},{3,3,3,3,3},{4,4,4,4,4}},categories,6));
    const auto best=optimize({{1,1,1,6,6},{6,6,6,1,1}},categories,6);
    assert(best && best->total==30 && best->categories==std::vector<std::size_t>({1,2}));
    const std::vector<Category> ties{{RuleKind::value_sum,2},{RuleKind::value_sum,2}};
    const auto tie=optimize({{2,2,1,1,1}},ties,6); assert(tie && tie->categories==std::vector<std::size_t>({0}));
    assert(!optimize({{0,1,2,3,4}},categories,6));
    const auto group=optimize({{5,5,5,1,2}},categories,6); assert(group && group->total==15);
    return 0;
}
'''


JOKER = r'''#pragma once
#include <algorithm>
#include <array>
#include <map>
#include <optional>
namespace charm::yacht {
enum class JokerCategory { yacht, full_house, four_kind, choice };
inline int fixed_joker_score(const std::array<int,5>& dice, JokerCategory category) {
    std::map<int,int> counts; int sum=0; for(int die:dice){++counts[die];sum+=die;}
    if(category==JokerCategory::choice) return sum;
    if(category==JokerCategory::yacht) return counts.size()==1 ? 50 : 0;
    if(category==JokerCategory::full_house) { bool two=false,three=false; for(const auto& item:counts){two=two||item.second==2;three=three||item.second==3;} return two&&three?25:0; }
    for(const auto& item:counts) if(item.second>=4) return sum;
    return 0;
}
inline std::optional<int> joker_score(const std::array<int,5>& dice, JokerCategory category) {
    int jokers=0; for(int die:dice){if(die==0)++jokers;else if(die<1||die>6)return std::nullopt;}
    if(jokers>1)return std::nullopt;
    if(jokers==0)return fixed_joker_score(dice,category);
    int best=0;
    for(int face=1;face<=6;++face){auto replaced=dice; for(int& die:replaced)if(die==0)die=face; best=std::max(best,fixed_joker_score(replaced,category));}
    return best;
}
}
'''
JOKER_START = JOKER.replace("if(jokers>1)return std::nullopt;", "if(jokers>0)return std::nullopt;")
JOKER_TEST = r'''#include "joker-rule-repair.h"
#include <array>
#include <cassert>
using charm::yacht::JokerCategory;
using charm::yacht::joker_score;
int main() {
    assert(!joker_score({0,0,1,2,3},JokerCategory::choice));
    assert(!joker_score({7,1,2,3,4},JokerCategory::choice));
    assert(joker_score({6,6,6,6,6},JokerCategory::yacht)==50);
    assert(joker_score({0,6,6,6,6},JokerCategory::yacht)==50);
    assert(joker_score({0,2,2,3,3},JokerCategory::full_house)==25);
    assert(joker_score({0,4,4,4,2},JokerCategory::four_kind)==18);
    assert(joker_score({0,1,2,3,4},JokerCategory::choice)==16);
    assert(joker_score({1,2,3,4,5},JokerCategory::four_kind)==0);
    return 0;
}
'''


def tasks() -> list[dict]:
    score_files = ["configurable-dice-score.h", "configurable-dice-score.cpp"]
    assign_files = ["scorecard-assignment.cpp"]
    joker_files = ["joker-rule-repair.h", "joker-rule-repair.cpp"]
    assign_prompt = calibration_prompt("Scorecard assignment", "Assign each five-die roll to a distinct category for maximum total; among equal totals return the lexicographically smallest category-index vector. Categories use the same value_sum, exact_group, and straight argument domains and formulas as configurable score. A roll/category pair with invalid dice, invalid arguments, or an unrepresentable score is unavailable; reject when no complete assignment exists.", "namespace charm::yacht { enum class RuleKind { exact_group, straight, value_sum }; struct Category { RuleKind kind; int argument; }; struct Assignment { int total; std::vector<std::size_t> categories; }; std::optional<Assignment> optimize(const std::vector<std::vector<int>>&,const std::vector<Category>&,int); }", ["empty rolls score zero", "more rolls than categories reject", "categories beyond size_t bit capacity reject", "categories cannot repeat", "ties choose lexical index vector"], assign_files)
    rows = [
        package(topic="Yacht", task_id="charm-v1-configurable-dice-score", instructions=prompt("Configurable dice score", "Validate exactly five dice. value_sum uses argument as a face in 1..sides and scores that face times its count. exact_group uses argument as an exact multiplicity in 1..5 and scores the highest face occurring exactly that many times, or zero. straight uses argument as the required number of distinct consecutive faces in 1..5 and scores the sum of those distinct faces, or zero. Unrepresentable scores reject.", "namespace charm::yacht { enum class RuleKind { exact_group, straight, value_sum }; struct Category { RuleKind kind; int argument; }; std::optional<int> score(const std::vector<int>&,int,Category); }", ["sides is positive", "every die lies in 1..sides", "category arguments validate", "exact group chooses highest matching face", "failed valid categories score zero"], score_files), editable={score_files[0]: "#pragma once\nnamespace charm::yacht {}\n", score_files[1]: support(score_files[0], 151)}, reference={score_files[0]: SCORE, score_files[1]: support(score_files[0], 152)}, hidden_name="configurable-dice-score_test.cpp", hidden=SCORE_TEST, category="configurable-rules", tags=["hidden-test-repair", "validation", "categories", "header-repair"]),
        package(topic="Yacht", task_id="charm-v1-scorecard-assignment", instructions=assign_prompt, editable={assign_files[0]: ASSIGN}, reference={assign_files[0]: ASSIGN}, hidden_name="scorecard-assignment_test.cpp", hidden=ASSIGN_TEST, category="optimal-assignment", tags=["calibration", "no-change", "backtracking", "tie-break"]),
        package(topic="Yacht", task_id="charm-v1-joker-rule-repair", instructions=prompt("Joker rule repair", "Score five dice with at most one zero joker by replacing it with one face from 1 through 6 and maximizing the selected category. yacht scores 50 only for five equal faces; full_house scores 25 only for exact 2+3 groups; four_kind scores the sum of all five dice when a face occurs at least four times; choice always scores the sum.", "namespace charm::yacht { enum class JokerCategory { yacht, full_house, four_kind, choice }; std::optional<int> joker_score(const std::array<int,5>&,JokerCategory); }", ["more than one joker rejects", "nonjoker faces are 1..6", "replacement is one face", "full house requires 2+3", "choice maximizes the sum"], joker_files), editable={joker_files[0]: JOKER_START, joker_files[1]: support(joker_files[0], 153)}, reference={joker_files[0]: JOKER, joker_files[1]: support(joker_files[0], 154)}, hidden_name="joker-rule-repair_test.cpp", hidden=JOKER_TEST, category="joker-substitution", tags=["partial", "joker", "maximization", "header-frozen"]),
    ]
    for row in rows:
        row["release_version"] = "v002"
    return rows
