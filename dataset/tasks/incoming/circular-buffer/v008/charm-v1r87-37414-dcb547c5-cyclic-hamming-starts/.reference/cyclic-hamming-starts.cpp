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

namespace charm::v1r87_37414::circular_buffer {

std::optional<std::vector<std::size_t>> cyclic_hamming_starts(std::string_view text, std::string_view pattern, std::size_t mismatch_budget);
}

namespace charm::v1r87_37414::circular_buffer {
std::optional<std::vector<std::size_t>> cyclic_hamming_starts(std::string_view text, std::string_view pattern, std::size_t mismatch_budget) {
if(text.empty()||pattern.empty())return std::nullopt;
std::vector<std::size_t> out;
for(std::size_t s=0;s<text.size();++s){std::size_t bad=0;
for(std::size_t j=0;j<pattern.size()&&bad<=mismatch_budget;++j)bad+=text[(s+j)%text.size()]!=pattern[j];
if(bad<=mismatch_budget)out.push_back(s);
}return out;

}
}
