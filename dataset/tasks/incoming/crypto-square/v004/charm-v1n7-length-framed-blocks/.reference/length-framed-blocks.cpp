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

std::optional<std::string> frame_normalized_blocks(std::string_view text, std::size_t width, char separator);
}

std::optional<std::string> charm::v1n7::crypto_square::frame_normalized_blocks(std::string_view text,std::size_t width,char separator){if(width==0||width>99||std::isalnum(static_cast<unsigned char>(separator)))return std::nullopt;std::string clean;for(char c:text)if(std::isalnum(static_cast<unsigned char>(c)))clean.push_back(static_cast<char>(std::toupper(static_cast<unsigned char>(c))));std::string out;for(std::size_t i=0;i<clean.size();i+=width){if(!out.empty())out.push_back(separator);std::size_t count=std::min(width,clean.size()-i);out+=std::to_string(count);out.push_back(':');out.append(clean,i,count);}return out;}
