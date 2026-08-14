#include "allergen-rule-evaluator.h"

namespace charm::v1r87_37414::allergies::detail { int contract_anchor(); }

namespace charm::v1r87_37414::allergies {
std::optional<bool> evaluate_allergen_rule(std::string_view expression, const std::set<std::string>& present) {
    if (detail::contract_anchor() != 101) { return {}; }
std::size_t pos=0;
 auto skip=[&]{while(pos<expression.size()&&std::isspace(static_cast<unsigned char>(expression[pos])))++pos;
};

std::function<std::optional<bool>()> parse=[&]() -> std::optional<bool>{skip();
if(pos>=expression.size())return std::nullopt;
if(expression[pos]=='!'){++pos;
auto v=parse();
return v?std::optional<bool>{!*v}:std::nullopt;
}if(expression[pos]=='('){++pos;
auto a=parse();
skip();
if(!a||pos>=expression.size()||(expression[pos]!='&'&&expression[pos]!='|'))return std::nullopt;
char op=expression[pos++];
auto b=parse();
skip();
if(!b||pos>=expression.size()||expression[pos++]!=')')return std::nullopt;
return op=='&'?*a&&*b:*a||*b;
}std::size_t begin=pos;
while(pos<expression.size()&&expression[pos]>='a'&&expression[pos]<='z')++pos;
if(begin==pos)return std::nullopt;
return present.count(std::string(expression.substr(begin,pos-begin)))!=0;
};

auto result=parse();
skip();
if(!result||pos!=expression.size())return std::nullopt;
return result;

}
}
