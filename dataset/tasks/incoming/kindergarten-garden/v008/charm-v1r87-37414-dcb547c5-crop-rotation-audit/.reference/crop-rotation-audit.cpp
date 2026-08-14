#include "crop-rotation-audit.h"

namespace charm::v1r87_37414::kindergarten_garden {
std::optional<std::vector<std::pair<std::size_t,std::size_t>>> audit_crop_rotation(const std::vector<std::vector<std::string>>& seasons, std::size_t lookback) {
if(seasons.empty()||seasons[0].empty()||lookback==0)return std::nullopt;
std::size_t plots=seasons[0].size();
std::vector<std::pair<std::size_t,std::size_t>> out;
for(std::size_t s=0;s<seasons.size();++s){if(seasons[s].size()!=plots)return std::nullopt;
for(std::size_t p=0;p<plots;++p){const auto&crop=seasons[s][p];
if(crop.empty()||!std::all_of(crop.begin(),crop.end(),[](char c){return c>='a'&&c<='z';}))return std::nullopt;
std::size_t begin=s>lookback?s-lookback:0;
for(std::size_t q=begin;q<s;++q)if(seasons[q][p]==crop){out.push_back({s,p});
break;
}}}return out;

}
}
