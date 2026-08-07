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

namespace charm::v1n7::spiral_matrix {

std::optional<std::vector<std::vector<int>>> fill_spiral_from_values(std::size_t rows, std::size_t columns, const std::vector<int>& values);
}

std::optional<std::vector<std::vector<int>>> charm::v1n7::spiral_matrix::fill_spiral_from_values(std::size_t rows,std::size_t columns,const std::vector<int>& values){if(rows!=0&&columns>std::numeric_limits<std::size_t>::max()/rows)return std::nullopt;if(values.size()!=rows*columns)return std::nullopt;std::vector<std::vector<int>> matrix(rows,std::vector<int>(columns));if(values.empty())return matrix;std::size_t top=0,bottom=rows-1,left=0,right=columns-1,index=0;while(top<=bottom&&left<=right){for(std::size_t c=left;c<=right;++c)matrix[top][c]=values[index++];if(++top>bottom)break;for(std::size_t r=top;r<=bottom;++r)matrix[r][right]=values[index++];if(right--==0||left>right)break;for(std::size_t c=right+1;c-->left;)matrix[bottom][c]=values[index++];if(bottom--==0||top>bottom)break;for(std::size_t r=bottom+1;r-->top;)matrix[r][left]=values[index++];++left;}return matrix;}
