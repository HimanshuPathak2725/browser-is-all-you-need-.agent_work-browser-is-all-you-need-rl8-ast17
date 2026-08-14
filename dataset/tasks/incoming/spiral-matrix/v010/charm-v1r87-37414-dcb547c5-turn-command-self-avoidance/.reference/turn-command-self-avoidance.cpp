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

namespace charm::v1r87_37414::spiral_matrix {
using GridPoint = std::pair<int,int>;
std::optional<std::vector<GridPoint>> replay_self_avoiding_turns(std::string_view commands);
}

namespace charm::v1r87_37414::spiral_matrix {
std::optional<std::vector<GridPoint>> replay_self_avoiding_turns(std::string_view commands) {
int r=0,c=0,dir=0;
const int dr[4]={-1,0,1,0},dc[4]={0,1,0,-1};
std::set<GridPoint> seen{{0,0}};
std::vector<GridPoint> out{{0,0}};
for(char ch:commands){if(ch=='L')dir=(dir+3)%4;
else if(ch=='R')dir=(dir+1)%4;
else if(ch=='F'){if((dr[dir]<0&&r==std::numeric_limits<int>::min())||(dr[dir]>0&&r==std::numeric_limits<int>::max())||(dc[dir]<0&&c==std::numeric_limits<int>::min())||(dc[dir]>0&&c==std::numeric_limits<int>::max()))return std::nullopt;
r+=dr[dir];
c+=dc[dir];
if(!seen.insert({r,c}).second)return std::nullopt;
out.push_back({r,c});
}else return std::nullopt;
}return out;

}
}
