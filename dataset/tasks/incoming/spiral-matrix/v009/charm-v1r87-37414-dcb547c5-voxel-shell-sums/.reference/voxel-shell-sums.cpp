#include "voxel-shell-sums.h"

namespace charm::v1r87_37414::spiral_matrix {
std::optional<std::vector<std::int64_t>> voxel_shell_sums(const std::vector<std::vector<std::vector<int>>>& box) {
if(box.empty()||box[0].empty()||box[0][0].empty())return std::nullopt;
std::size_t z=box.size(),y=box[0].size(),x=box[0][0].size();
for(const auto&plane:box){if(plane.size()!=y)return std::nullopt;
for(const auto&row:plane)if(row.size()!=x)return std::nullopt;
}std::size_t shells=(std::min({z,y,x})+1)/2;
std::vector<std::int64_t> out(shells);
for(std::size_t a=0;a<z;++a)for(std::size_t b=0;b<y;++b)for(std::size_t c=0;c<x;++c){auto d=std::min({a,z-1-a,b,y-1-b,c,x-1-c});
auto v=box[a][b][c];
if((v>0&&out[d]>std::numeric_limits<std::int64_t>::max()-v)||(v<0&&out[d]<std::numeric_limits<std::int64_t>::min()-v))return std::nullopt;
out[d]+=v;
}return out;

}
}
