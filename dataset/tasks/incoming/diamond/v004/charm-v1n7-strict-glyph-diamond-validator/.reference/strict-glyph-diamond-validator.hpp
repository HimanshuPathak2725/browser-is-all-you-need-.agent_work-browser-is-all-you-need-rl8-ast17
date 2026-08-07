#pragma once

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

bool is_strict_glyph_diamond(const std::vector<std::string>& rows, char ink, char fill);
}

inline bool charm::v1n7::diamond::is_strict_glyph_diamond(const std::vector<std::string>& rows,char ink,char fill){if(ink==fill||rows.empty()||rows.size()%2==0)return false;std::size_t width=rows.size();for(const auto& row:rows)if(row.size()!=width)return false;long long radius=static_cast<long long>(width/2);for(std::size_t y=0;y<width;++y)for(std::size_t x=0;x<width;++x){bool inside=std::llabs(static_cast<long long>(x)-radius)+std::llabs(static_cast<long long>(y)-radius)<=radius;if(rows[y][x]!=(inside?ink:fill))return false;}return true;}
