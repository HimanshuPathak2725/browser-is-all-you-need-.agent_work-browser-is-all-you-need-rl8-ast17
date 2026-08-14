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

namespace charm::v1r87_37414::sublist {

std::optional<std::vector<std::size_t>> confirmed_rolling_hash_matches(std::string_view text, std::string_view pattern, std::uint64_t base);
}

namespace charm::v1r87_37414::sublist {
std::optional<std::vector<std::size_t>> confirmed_rolling_hash_matches(std::string_view text, std::string_view pattern, std::uint64_t base) {
if(pattern.empty()||base<=1||base%2==0)return std::nullopt;
std::vector<std::size_t> out;
if(pattern.size()>text.size())return out;
std::uint64_t hp=0,hw=0,power=1;
for(std::size_t i=0;i<pattern.size();++i){hp=hp*base+static_cast<unsigned char>(pattern[i])+1;
hw=hw*base+static_cast<unsigned char>(text[i])+1;
if(i+1<pattern.size())power*=base;
}for(std::size_t i=0;;++i){if(hw==hp&&text.substr(i,pattern.size())==pattern)out.push_back(i);
if(i+pattern.size()==text.size())break;
hw-=power*(static_cast<unsigned char>(text[i])+1);
hw=hw*base+static_cast<unsigned char>(text[i+pattern.size()])+1;
}return out;

}
}
