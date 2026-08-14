#include <algorithm>
#include <array>
#include <cctype>
#include <climits>
#include <cstdlib>
#include <future>
#include <cmath>
#include <complex>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <functional>
#include <iterator>
#include <limits>
#include <map>
#include <memory>
#include <numeric>
#include <optional>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace charm::v1r87_37414::allergies {

std::optional<std::vector<std::size_t>> minimum_cleaning_cover(const std::vector<std::uint32_t>& procedure_masks, std::uint32_t required_mask, std::uint32_t known_mask);
}

namespace charm::v1r87_37414::allergies {
std::optional<std::vector<std::size_t>> minimum_cleaning_cover(const std::vector<std::uint32_t>& procedure_masks, std::uint32_t required_mask, std::uint32_t known_mask) {
if((required_mask&~known_mask)!=0||procedure_masks.size()>20){return std::nullopt;
}for(auto m:procedure_masks)if((m&~known_mask)!=0)return std::nullopt;

std::vector<std::size_t> best;
bool found=false;
const std::uint64_t limit=std::uint64_t{1}<<procedure_masks.size();
for(std::uint64_t bits=0;bits<limit;++bits){std::uint32_t cover=0;
std::vector<std::size_t> pick;
for(std::size_t i=0;i<procedure_masks.size();++i)if(bits&(std::uint64_t{1}<<i)){cover|=procedure_masks[i];
pick.push_back(i);
}if((cover&required_mask)!=required_mask)continue;
if(!found||pick.size()<best.size()||(pick.size()==best.size()&&pick<best)){best=pick;
found=true;
}}if(!found)return std::vector<std::size_t>{};
return best;

}
}
