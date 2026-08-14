#include "minimum-substring-block-cover.h"

namespace charm::v1r87_37414::sublist {
std::optional<BlockCoverResult> minimum_substring_block_cover(std::string_view source, std::string_view target) {
if(target.empty())return std::nullopt;
const std::size_t inf=target.size()+1;
std::vector<std::size_t> dp(target.size()+1,inf);
dp[0]=0;
for(std::size_t i=0;i<target.size();++i)if(dp[i]<inf)for(std::size_t j=i+1;j<=target.size();++j)if(source.find(target.substr(i,j-i))!=std::string_view::npos)dp[j]=std::min(dp[j],dp[i]+1);
if(dp.back()==inf)return BlockCoverResult{false,0};
return BlockCoverResult{true,dp.back()};

}
}
