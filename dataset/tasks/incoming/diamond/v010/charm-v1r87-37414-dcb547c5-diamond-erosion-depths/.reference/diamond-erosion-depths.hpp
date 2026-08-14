#pragma once

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

namespace charm::v1r87_37414::diamond {

std::optional<std::vector<std::vector<int>>> diamond_erosion_depths(const std::vector<std::string>& grid);
}

namespace charm::v1r87_37414::diamond {
inline std::optional<std::vector<std::vector<int>>> diamond_erosion_depths(const std::vector<std::string>& grid) {
if(grid.empty()||grid[0].empty())return std::nullopt;
std::size_t h=grid.size(),w=grid[0].size();
for(const auto&r:grid)if(r.size()!=w||!std::all_of(r.begin(),r.end(),[](char c){return c=='#'||c=='.';}))return std::nullopt;
std::vector<std::vector<int>> d(h,std::vector<int>(w,-1));
std::queue<std::pair<int,int>> q;
for(int r=0;r<(int)h;++r)for(int c=0;c<(int)w;++c)if(grid[r][c]=='.'){d[r][c]=0;
q.push({r,c});
}
else if(r==0||c==0||r+1==(int)h||c+1==(int)w){d[r][c]=1;
q.push({r,c});
}
const int dr[4]={1,-1,0,0},dc[4]={0,0,1,-1};
while(!q.empty()){auto [r,c]=q.front();
q.pop();
for(int k=0;k<4;++k){int a=r+dr[k],b=c+dc[k];
if(a>=0&&b>=0&&a<(int)h&&b<(int)w&&grid[a][b]=='#'&&d[a][b]<0){d[a][b]=d[r][c]+1;
q.push({a,b});
}}}
return d;

}
}
