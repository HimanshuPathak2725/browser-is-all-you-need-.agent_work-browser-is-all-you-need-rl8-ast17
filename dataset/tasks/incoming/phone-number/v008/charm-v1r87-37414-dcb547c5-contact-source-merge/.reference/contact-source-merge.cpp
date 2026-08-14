#include "contact-source-merge.h"

namespace charm::v1r87_37414::phone_number {
std::optional<std::map<std::string,std::string>> merge_contact_sources(const std::vector<ContactRecord>& records) {
std::map<std::string,std::pair<int,std::string>> best;
for(const auto&r:records){if(r.name.empty()||r.number.empty()||!std::all_of(r.name.begin(),r.name.end(),[](char c){return c>='a'&&c<='z';})||!std::all_of(r.number.begin(),r.number.end(),[](char c){return c>='0'&&c<='9';})||r.priority<0)return std::nullopt;
auto it=best.find(r.name);
if(it==best.end()||r.priority<it->second.first)best[r.name]={r.priority,r.number};
else if(r.priority==it->second.first&&r.number!=it->second.second)return std::nullopt;
}std::map<std::string,std::string> out;
for(auto&[n,p]:best)out[n]=p.second;
return out;

}
}
