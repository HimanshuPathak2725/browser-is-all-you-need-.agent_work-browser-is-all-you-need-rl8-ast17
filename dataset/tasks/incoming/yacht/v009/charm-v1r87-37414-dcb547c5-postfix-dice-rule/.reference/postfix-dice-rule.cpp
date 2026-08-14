#include "postfix-dice-rule.h"

namespace charm::v1r87_37414::yacht {
std::optional<std::int64_t> evaluate_postfix_dice_rule(const std::vector<int>& dice, const std::vector<std::string>& program) {
for(int d:dice)if(d<1||d>6)return std::nullopt;
std::vector<std::int64_t> st;
auto push_checked=[&](long long v){st.push_back(v);
};
for(const auto&t:program){if(t=="sum")st.push_back(std::accumulate(dice.begin(),dice.end(),std::int64_t{0}));
else if(t=="max"){if(dice.empty())return std::nullopt;
st.push_back(*std::max_element(dice.begin(),dice.end()));
}else if(t.rfind("count:",0)==0&&t.size()==7&&t[6]>='1'&&t[6]<='6')st.push_back(std::count(dice.begin(),dice.end(),t[6]-'0'));
else if(t=="+"||t=="*"){if(st.size()<2)return std::nullopt;
auto b=st.back();
st.pop_back();
auto a=st.back();
st.pop_back();
if(t=="+"&&a>std::numeric_limits<std::int64_t>::max()-b)return std::nullopt;
if(t=="*"&&a!=0&&b>std::numeric_limits<std::int64_t>::max()/a)return std::nullopt;
push_checked(t=="+"?a+b:a*b);
}else if(!t.empty()&&std::all_of(t.begin(),t.end(),[](char c){return c>='0'&&c<='9';})){std::uint64_t v=0;
for(char c:t){auto digit=static_cast<std::uint64_t>(c-'0');
auto limit=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
if(v>(limit-digit)/10)return std::nullopt;
v=v*10+digit;
}st.push_back(static_cast<std::int64_t>(v));
}else return std::nullopt;
}if(st.size()!=1)return std::nullopt;
return st[0];

}
}
