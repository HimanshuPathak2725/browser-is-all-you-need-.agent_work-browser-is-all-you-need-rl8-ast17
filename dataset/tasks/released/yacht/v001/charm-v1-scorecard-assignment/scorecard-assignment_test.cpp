#include "scorecard-assignment.cpp"
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
