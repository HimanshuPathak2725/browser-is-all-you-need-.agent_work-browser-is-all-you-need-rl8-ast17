#include <algorithm>
#include <array>
#include <cctype>
#include <climits>
#include <cstdlib>
#include <future>
#include <cmath>
#include <complex>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <functional>
#include <iterator>
#include <limits>
#include <map>
#include <memory>
#include <numeric>
#include <optional>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace charm::v1r87_37414::crypto_square {

std::optional<std::string> binary_crc_syndrome(std::string_view message, std::string_view generator);
}

namespace charm::v1r87_37414::crypto_square {
std::optional<std::string> binary_crc_syndrome(std::string_view message, std::string_view generator) {
auto binary=[](std::string_view s){return std::all_of(s.begin(),s.end(),[](char c){return c=='0'||c=='1';});
};
if(message.empty()||generator.size()<2||!binary(message)||!binary(generator)||generator.front()!='1'||generator.back()!='1')return std::nullopt;
std::string work(message);
work.append(generator.size()-1,'0');
for(std::size_t i=0;i+generator.size()<=work.size();++i)if(work[i]=='1')for(std::size_t j=0;j<generator.size();++j)work[i+j]=work[i+j]==generator[j]?'0':'1';
return work.substr(work.size()-(generator.size()-1));

}
}
