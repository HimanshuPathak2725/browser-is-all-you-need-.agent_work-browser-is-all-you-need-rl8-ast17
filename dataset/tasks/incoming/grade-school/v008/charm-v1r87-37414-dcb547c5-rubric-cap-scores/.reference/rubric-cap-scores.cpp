#include "rubric-cap-scores.h"

namespace charm::v1r87_37414::grade_school {
std::optional<std::map<std::string,std::int64_t>> score_capped_rubrics(const std::map<std::string,std::int64_t>& caps, const std::map<std::string,std::map<std::string,std::int64_t>>& submissions) {
for(auto [k,v]:caps)if(k.empty()||v<=0)return std::nullopt;
std::map<std::string,std::int64_t> out;
for(const auto&[student,points]:submissions){if(student.empty())return std::nullopt;
std::int64_t total=0;
for(auto [name,value]:points){auto it=caps.find(name);
if(it==caps.end()||value<0)return std::nullopt;
auto add=std::min(value,it->second);
if(total>std::numeric_limits<std::int64_t>::max()-add)return std::nullopt;
total+=add;
}out[student]=total;
}return out;

}
}
