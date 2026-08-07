#include <algorithm>
#include <array>
#include <climits>
#include <cstdlib>
#include <future>
#include <cmath>
#include <complex>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <functional>
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

namespace charm::v1n7::diamond {

std::optional<std::vector<std::string>> render_layered_diamond(int radius);
}

std::optional<std::vector<std::string>> charm::v1n7::diamond::render_layered_diamond(int radius){if(radius<0||radius>14)return std::nullopt;int width=2*radius+1;std::vector<std::string> out(static_cast<std::size_t>(width),std::string(static_cast<std::size_t>(width),'.'));const char* digits="0123456789abcdef";for(int y=-radius;y<=radius;++y)for(int x=-radius;x<=radius;++x){int d=std::abs(x)+std::abs(y);if(d<=radius)out[static_cast<std::size_t>(y+radius)][static_cast<std::size_t>(x+radius)]=digits[radius-d+1];}return out;}
