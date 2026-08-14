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

namespace charm::v1r87_37414::complex_numbers {

std::optional<std::vector<std::complex<double>>> sample_complex_bezier(const std::vector<std::complex<double>>& control, const std::vector<std::pair<std::int64_t,std::int64_t>>& parameters);
}

namespace charm::v1r87_37414::complex_numbers {
std::optional<std::vector<std::complex<double>>> sample_complex_bezier(const std::vector<std::complex<double>>& control, const std::vector<std::pair<std::int64_t,std::int64_t>>& parameters) {
if(control.empty())return std::nullopt;
std::vector<std::complex<double>> out;
for(auto [n,d]:parameters){if(d<=0||n<0||n>d)return std::nullopt;
double t=static_cast<double>(n)/d;
auto work=control;
for(std::size_t width=work.size();width>1;--width)for(std::size_t i=0;i+1<width;++i)work[i]=work[i]*(1-t)+work[i+1]*t;
out.push_back(work[0]);
}return out;

}
}
