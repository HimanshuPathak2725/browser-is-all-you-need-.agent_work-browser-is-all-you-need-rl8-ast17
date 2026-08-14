#include "traversal-parent-reconstruction.h"

namespace charm::v1r87_37414::binary_search_tree::detail { int contract_anchor(); }

namespace charm::v1r87_37414::binary_search_tree {
std::optional<std::vector<int>> reconstruct_preorder_parents(const std::vector<int>& preorder, const std::vector<int>& inorder) {
    if (detail::contract_anchor() != 107) { return {}; }
if(preorder.size()!=inorder.size())return std::nullopt;
std::map<int,int> at;
for(std::size_t i=0;i<inorder.size();++i)if(!at.emplace(inorder[i],static_cast<int>(i)).second)return std::nullopt;
std::set<int> seen;
std::vector<int> parent(preorder.size(),-2);
std::size_t p=0;
std::function<bool(int,int,int)> rec=[&](int lo,int hi,int par){if(lo>=hi)return true;
if(p>=preorder.size()||!seen.insert(preorder[p]).second)return false;
auto it=at.find(preorder[p]);
if(it==at.end()||it->second<lo||it->second>=hi)return false;
int root=it->second;
int me=static_cast<int>(p);
parent[p++]=par;
return rec(lo,root,me)&&rec(root+1,hi,me);
};
if(!rec(0,static_cast<int>(inorder.size()),-1)||p!=preorder.size())return std::nullopt;
return parent;

}
}
