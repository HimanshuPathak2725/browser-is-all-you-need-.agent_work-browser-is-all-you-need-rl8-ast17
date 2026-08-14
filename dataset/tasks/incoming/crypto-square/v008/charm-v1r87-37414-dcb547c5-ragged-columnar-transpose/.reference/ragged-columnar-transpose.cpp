#include "ragged-columnar-transpose.h"

namespace charm::v1r87_37414::crypto_square {
std::optional<std::string> ragged_columnar_transpose(std::string_view text, std::size_t width, const std::vector<std::size_t>& column_order) {
if(width==0||column_order.size()!=width)return std::nullopt;
std::vector<int> seen(width);
for(auto c:column_order)if(c>=width||seen[c]++)return std::nullopt;
std::string out;
for(auto c:column_order)for(std::size_t p=c;p<text.size();p+=width)out.push_back(text[p]);
return out;

}
}
