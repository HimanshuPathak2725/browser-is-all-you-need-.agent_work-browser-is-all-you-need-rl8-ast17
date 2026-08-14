#include "parallel-anagram-groups.h"

namespace charm::v1r87_37414::parallel_letter_frequency {
std::optional<std::vector<std::vector<std::string>>> parallel_anagram_groups(const std::vector<std::string>& words, std::size_t workers) {
if(workers==0)return std::nullopt;
for(const auto&w:words)if(w.empty()||!std::all_of(w.begin(),w.end(),[](char c){return c>='a'&&c<='z';}))return std::nullopt;
std::size_t jobs=std::min(workers,std::max<std::size_t>(1,words.size()));
std::vector<std::future<std::map<std::string,std::vector<std::string>>>> fs;
for(std::size_t j=0;j<jobs;++j)fs.push_back(std::async(std::launch::async,[&,j]{std::map<std::string,std::vector<std::string>> m;for(std::size_t i=j;i<words.size();i+=jobs){auto key=words[i];std::sort(key.begin(),key.end());m[key].push_back(words[i]);}return m;}));
std::map<std::string,std::vector<std::string>> all;
for(auto&f:fs)for(auto&[k,v]:f.get())all[k].insert(all[k].end(),v.begin(),v.end());
std::vector<std::vector<std::string>> out;
for(auto&[k,v]:all){std::sort(v.begin(),v.end());
out.push_back(v);
}std::sort(out.begin(),out.end(),[](const auto&a,const auto&b){return a[0]<b[0];});
return out;

}
}
