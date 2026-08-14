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

namespace charm::v1r87_37414::parallel_letter_frequency {

std::optional<std::array<std::size_t,26>> parallel_caesar_coincidences(std::string_view left, std::string_view right, std::size_t workers);
}

namespace charm::v1r87_37414::parallel_letter_frequency {
std::optional<std::array<std::size_t,26>> parallel_caesar_coincidences(std::string_view left, std::string_view right, std::size_t workers) {
if(workers==0||left.size()!=right.size()||!std::all_of(left.begin(),left.end(),[](char c){return c>='a'&&c<='z';})||!std::all_of(right.begin(),right.end(),[](char c){return c>='a'&&c<='z';}))return std::nullopt;
std::size_t jobs=std::min<std::size_t>(workers,26);
std::vector<std::future<std::vector<std::pair<int,std::size_t>>>> fs;
for(std::size_t j=0;j<jobs;++j)fs.push_back(std::async(std::launch::async,[&,j]{std::vector<std::pair<int,std::size_t>> v;for(int s=static_cast<int>(j);s<26;s+=jobs){std::size_t n=0;for(std::size_t i=0;i<left.size();++i)n+=((left[i]-'a'+s)%26)==right[i]-'a';v.push_back({s,n});}return v;}));
std::array<std::size_t,26> out{};
for(auto&f:fs)for(auto [s,n]:f.get())out[s]=n;
return out;

}
}
