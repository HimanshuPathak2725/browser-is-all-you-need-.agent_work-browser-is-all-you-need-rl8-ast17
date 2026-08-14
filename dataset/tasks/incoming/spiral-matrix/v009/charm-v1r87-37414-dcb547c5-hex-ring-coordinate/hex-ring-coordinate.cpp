#include "hex-ring-coordinate.h"

namespace charm::v1r87_37414::spiral_matrix {
std::optional<AxialPoint> hex_ring_coordinate(std::uint64_t steps) {
if(steps==1)return AxialPoint{0,0};
std::uint64_t ring=1,base=1;
while(steps>=base+6*ring){base+=6*ring;
++ring;
if(ring>static_cast<std::uint64_t>(std::numeric_limits<int>::max()))return std::nullopt;
}std::uint64_t offset=steps-base;
long long q=ring,r=0;
const int dq[6]={-1,-1,0,1,1,0},dr[6]={1,0,-1,-1,0,1};
for(int side=0;side<6;++side){auto take=std::min<std::uint64_t>(ring,offset);
q+=dq[side]*static_cast<long long>(take);
r+=dr[side]*static_cast<long long>(take);
offset-=take;
if(!offset)break;
}if(q<std::numeric_limits<int>::min()||q>std::numeric_limits<int>::max()||r<std::numeric_limits<int>::min()||r>std::numeric_limits<int>::max())return std::nullopt;
return AxialPoint{static_cast<int>(q),static_cast<int>(r)};

}
}
