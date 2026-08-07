#include <algorithm>
#include <functional>
#include <optional>
#include <vector>
namespace charm::yacht {
enum class RuleKind { exact_group, straight, value_sum };
struct Category { RuleKind kind; int argument; };
struct Assignment { int total; std::vector<std::size_t> categories; };
static std::optional<int> assignment_score(const std::vector<int>& dice, int sides, Category category) {
    if (dice.size() != 5 || sides < 1) return std::nullopt;
    std::vector<int> counts(static_cast<std::size_t>(sides + 1));
    for (int die : dice) { if (die < 1 || die > sides) return std::nullopt; ++counts[static_cast<std::size_t>(die)]; }
    if (category.kind == RuleKind::value_sum) return category.argument >= 1 && category.argument <= sides ? std::optional<int>(category.argument * counts[category.argument]) : std::nullopt;
    if (category.kind == RuleKind::exact_group) { if (category.argument < 1 || category.argument > 5) return std::nullopt; int best=0; for(int face=1;face<=sides;++face) if(counts[face]==category.argument) best=std::max(best,face*counts[face]); return best; }
    if (category.argument < 1 || category.argument > 5) return std::nullopt;
    int first=0, unique=0, total=0; for(int face=1;face<=sides;++face) if(counts[face]) { if(!first) first=face; if(face!=first+unique) return 0; ++unique; total+=face; }
    return unique==category.argument ? total : 0;
}
inline std::optional<Assignment> optimize(const std::vector<std::vector<int>>& rolls, const std::vector<Category>& categories, int sides) {
    if (rolls.size() > categories.size()) return std::nullopt;
    Assignment best{-1,{}}; std::vector<bool> used(categories.size()); std::vector<std::size_t> chosen;
    std::function<bool(std::size_t,int)> search = [&](std::size_t roll, int total) {
        if (roll == rolls.size()) { if (total > best.total || (total == best.total && chosen < best.categories)) best={total,chosen}; return true; }
        bool valid=false;
        for(std::size_t category=0;category<categories.size();++category) if(!used[category]) {
            const auto value=assignment_score(rolls[roll],sides,categories[category]); if(!value) continue;
            used[category]=true; chosen.push_back(category); valid=search(roll+1,total+*value)||valid; chosen.pop_back(); used[category]=false;
        }
        return valid;
    };
    return search(0,0) ? std::optional<Assignment>(best) : std::nullopt;
}
}
