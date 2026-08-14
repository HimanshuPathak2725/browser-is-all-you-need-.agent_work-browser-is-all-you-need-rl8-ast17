#include "manhattan-voronoi-owners.h"

namespace charm::v1r87_37414::diamond {
std::optional<std::vector<int>> manhattan_voronoi_owners(const std::vector<LatticePoint>& sites, const std::vector<LatticePoint>& queries) {
if(std::set<LatticePoint>(sites.begin(),sites.end()).size()!=sites.size())return std::nullopt;
std::vector<int> out;
for(auto q:queries){if(sites.empty()){out.push_back(-1);
continue;
}std::uint64_t best=std::numeric_limits<std::uint64_t>::max();
int owner=-1;
bool tie=false;
for(std::size_t i=0;i<sites.size();++i){auto delta=[](std::int64_t a,std::int64_t b)->std::optional<std::uint64_t>{if((b>0&&a<std::numeric_limits<std::int64_t>::min()+b)||(b<0&&a>std::numeric_limits<std::int64_t>::max()+b))return std::nullopt;
auto d=a-b;
return d<0?std::uint64_t(-(d+1))+1:std::uint64_t(d);
};
auto dx=delta(q.first,sites[i].first),dy=delta(q.second,sites[i].second);
if(!dx||!dy||*dx>std::numeric_limits<std::uint64_t>::max()-*dy)return std::nullopt;
auto d=*dx+*dy;
if(d<best){best=d;
owner=static_cast<int>(i);
tie=false;
}else if(d==best)tie=true;
}out.push_back(tie?-1:owner);
}return out;

}
}
