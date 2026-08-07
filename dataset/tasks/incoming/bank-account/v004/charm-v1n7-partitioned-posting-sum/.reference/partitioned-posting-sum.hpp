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

namespace charm::v1n7::bank_account {

std::optional<long long> partitioned_posting_sum(const std::vector<long long>& postings, std::size_t worker_count);
}

inline std::optional<long long> charm::v1n7::bank_account::partitioned_posting_sum(const std::vector<long long>& postings, std::size_t worker_count) {
    if (worker_count==0) return std::nullopt;
    if (postings.empty()) return 0LL;
    const std::size_t workers=std::min(worker_count,postings.size());
    std::vector<std::future<std::optional<long long>>> jobs;
    for (std::size_t w=0;w<workers;++w) jobs.push_back(std::async(std::launch::async,[&,w]{ long long sum=0; for(std::size_t i=w;i<postings.size();i+=workers){long long x=postings[i]; if((x>0&&sum>std::numeric_limits<long long>::max()-x)||(x<0&&sum<std::numeric_limits<long long>::min()-x))return std::optional<long long>{}; sum+=x;} return std::optional<long long>{sum}; }));
    long long total=0;
    for(auto& job:jobs){auto part=job.get();if(!part)return std::nullopt;long long x=*part;if((x>0&&total>std::numeric_limits<long long>::max()-x)||(x<0&&total<std::numeric_limits<long long>::min()-x))return std::nullopt;total+=x;}
    return total;
}
