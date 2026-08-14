#include "parallel-rare-offsets.h"

#include <algorithm>
#include <array>
#include <future>
namespace charm::v1r87_37414::parallel_letter_frequency {
std::optional<std::vector<std::size_t>> parallel_rare_letter_offsets(const std::vector<std::string>& lines, std::size_t workers) {
if(workers==0)return std::nullopt;
for(const auto&s:lines)if(!std::all_of(s.begin(),s.end(),[](char c){return c>='a'&&c<='z';}))return std::nullopt;
std::size_t jobs=std::min(workers,std::max<std::size_t>(1,lines.size()));
std::vector<std::future<std::array<std::size_t,26>>> fs;
for(std::size_t j=0;j<jobs;++j)fs.push_back(std::async(std::launch::async,[&,j]{std::array<std::size_t,26>a{};for(std::size_t i=j;i<lines.size();i+=jobs)for(char c:lines[i])++a[c-'a'];return a;}));
std::array<std::size_t,26> total{};
for(auto&f:fs){auto a=f.get();
for(int i=0;i<26;++i)total[i]+=a[i];
}
std::vector<std::size_t> out;
std::size_t offset=0;
for(const auto&s:lines)for(char c:s){if(total[c-'a']==1)out.push_back(offset);
++offset;
}
return out;

}
}
