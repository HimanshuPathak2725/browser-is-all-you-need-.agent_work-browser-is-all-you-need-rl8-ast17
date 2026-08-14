#include "paired-cohort-deltas.h"

namespace charm::v1r87_37414::grade_school {
std::optional<CohortDeltaSummary> summarize_paired_cohort_deltas(const std::map<std::string,int>& before, const std::map<std::string,int>& after) {
if(before.empty()||before.size()!=after.size())return std::nullopt;
std::vector<int>d;
CohortDeltaSummary s{0,0,0,0};
for(auto [name,a]:before){auto it=after.find(name);
if(name.empty()||it==after.end())return std::nullopt;
long long x=static_cast<long long>(it->second)-a;
if(x<std::numeric_limits<int>::min()||x>std::numeric_limits<int>::max())return std::nullopt;
d.push_back(static_cast<int>(x));
if(x>0)++s.improved;
else if(x<0)++s.declined;
else ++s.equal;
}std::sort(d.begin(),d.end());
s.lower_median=d[(d.size()-1)/2];
return s;

}
}
