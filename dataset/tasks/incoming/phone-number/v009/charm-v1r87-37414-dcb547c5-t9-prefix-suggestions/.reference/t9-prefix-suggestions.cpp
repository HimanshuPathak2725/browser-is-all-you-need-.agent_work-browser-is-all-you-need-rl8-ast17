#include "t9-prefix-suggestions.h"

namespace charm::v1r87_37414::phone_number {
std::optional<std::vector<std::string>> t9_prefix_suggestions(const std::vector<std::string>& contacts, std::string_view prefix, std::size_t limit) {
if(prefix.empty()||!std::all_of(prefix.begin(),prefix.end(),[](char c){return c>='2'&&c<='9';}))return std::nullopt;
std::set<std::string> unique;
auto digit=[](char c){const std::string groups="22233344455566677778889999";
return groups[c-'a'];
};
std::vector<std::string> out;
for(const auto&name:contacts){if(name.empty()||!std::all_of(name.begin(),name.end(),[](char c){return c>='a'&&c<='z';})||!unique.insert(name).second)return std::nullopt;
if(name.size()>=prefix.size()&&std::equal(prefix.begin(),prefix.end(),name.begin(),[&](char d,char c){return d==digit(c);}))out.push_back(name);
}std::sort(out.begin(),out.end());
if(out.size()>limit)out.resize(limit);
return out;

}
}
