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

namespace charm::v1n7::crypto_square {

std::optional<std::string> decode_checked_grid(std::string_view frame, std::size_t rows, std::size_t columns);
}

inline std::optional<std::string> charm::v1n7::crypto_square::decode_checked_grid(std::string_view frame,std::size_t rows,std::size_t columns){if(rows==0||columns==0||rows>std::numeric_limits<std::size_t>::max()/columns)return std::nullopt;std::size_t count=rows*columns;if(frame.size()!=count+1)return std::nullopt;unsigned sum=0;for(std::size_t i=0;i<count;++i)sum+=static_cast<unsigned char>(frame[i]);char expected="0123456789abcdef"[sum%16U];if(frame[count]!=expected)return std::nullopt;std::string out;out.reserve(count);for(std::size_t c=0;c<columns;++c)for(std::size_t r=0;r<rows;++r)out.push_back(frame[r*columns+c]);return out;}
