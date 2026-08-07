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

namespace charm::v1n7::parallel_letter_frequency {

std::optional<std::vector<std::size_t>> parallel_longest_letter_runs(const std::vector<std::string>& inputs, std::size_t worker_count);
}

std::optional<std::vector<std::size_t>> charm::v1n7::parallel_letter_frequency::parallel_longest_letter_runs(const std::vector<std::string>& inputs,std::size_t worker_count){if(worker_count==0)return std::nullopt;std::vector<std::size_t> result(inputs.size());if(inputs.empty())return result;std::size_t workers=std::min(worker_count,inputs.size());std::vector<std::future<void>> jobs;for(std::size_t w=0;w<workers;++w)jobs.push_back(std::async(std::launch::async,[&,w]{for(std::size_t i=w;i<inputs.size();i+=workers){std::size_t best=0,run=0;int previous=-1;for(unsigned char c:inputs[i]){int current=c<128&&std::isalpha(c)?std::tolower(c):-1;if(current>=0&&current==previous)++run;else run=current>=0?1U:0U;best=std::max(best,run);previous=current;}result[i]=best;}}));for(auto& job:jobs)job.get();return result;}
