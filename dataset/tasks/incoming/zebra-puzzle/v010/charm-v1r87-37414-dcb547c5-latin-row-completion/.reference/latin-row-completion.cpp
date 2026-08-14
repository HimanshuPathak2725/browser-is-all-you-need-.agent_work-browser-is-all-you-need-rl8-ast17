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

namespace charm::v1r87_37414::zebra_puzzle {

std::optional<std::vector<int>> complete_unique_latin_row(std::vector<std::vector<int>> grid, std::size_t row);
}

namespace charm::v1r87_37414::zebra_puzzle {
std::optional<std::vector<int>> complete_unique_latin_row(std::vector<std::vector<int>> grid, std::size_t row) {
std::size_t n=grid.size();
if(n==0||row>=n)return std::nullopt;
for(const auto&r:grid)if(r.size()!=n)return std::nullopt;
for(std::size_t r=0;r<n;++r)for(int v:grid[r])if(v<0||v>static_cast<int>(n)||(r!=row&&v==0))return std::nullopt;
std::vector<std::vector<int>> solutions;
std::function<void(std::size_t)> fill=[&](std::size_t c){if(c==n){for(std::size_t r=0;r<n;++r){std::set<int>s(grid[r].begin(),grid[r].end());
if(s.size()!=n||*s.begin()!=1||*s.rbegin()!=static_cast<int>(n))return;
}solutions.push_back(grid[row]);
return;
}if(grid[row][c]){fill(c+1);
return;
}for(int v=1;v<=static_cast<int>(n);++v){bool ok=true;
for(std::size_t k=0;k<n;++k)if(grid[row][k]==v||grid[k][c]==v)ok=false;
if(ok){grid[row][c]=v;
fill(c+1);
grid[row][c]=0;
}}};
for(std::size_t c=0;c<n;++c){std::set<int>s;
for(std::size_t r=0;r<n;++r)if(grid[r][c]&&!s.insert(grid[r][c]).second)return std::nullopt;
}fill(0);
if(solutions.size()!=1)return std::nullopt;
return solutions[0];

}
}
