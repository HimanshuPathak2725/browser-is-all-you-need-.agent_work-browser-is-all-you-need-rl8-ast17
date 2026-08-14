#include "wildcard-contiguous-matches.h"

namespace charm::v1r87_37414::sublist {
std::optional<std::vector<std::size_t>> wildcard_contiguous_matches(std::string_view text, std::string_view pattern) {
if(pattern.empty())return std::nullopt;
std::vector<std::size_t> out;
if(pattern.size()>text.size())return out;
for(std::size_t i=0;i+pattern.size()<=text.size();++i){bool ok=true;
for(std::size_t j=0;j<pattern.size();++j)if(pattern[j]!='?'&&pattern[j]!=text[i+j]){ok=false;
break;
}if(ok)out.push_back(i);
}return out;

}
}
