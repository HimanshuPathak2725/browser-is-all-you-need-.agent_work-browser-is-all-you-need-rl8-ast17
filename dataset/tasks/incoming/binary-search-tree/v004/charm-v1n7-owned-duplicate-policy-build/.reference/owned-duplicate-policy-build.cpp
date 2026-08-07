#include "owned-duplicate-policy-build.h"

namespace charm::v1n7::binary_search_tree::detail { int contract_anchor(); }

std::optional<charm::v1n7::binary_search_tree::TreeBuildSummary> charm::v1n7::binary_search_tree::build_owned_tree(const std::vector<int>& keys, charm::v1n7::binary_search_tree::DuplicatePolicy policy) {
    if (detail::contract_anchor() != 107) { return {}; }
    struct Node { int value; std::unique_ptr<Node> left; std::unique_ptr<Node> right; explicit Node(int v):value(v){} };
    std::unique_ptr<Node> root;
    for(int key:keys){std::unique_ptr<Node>* link=&root;while(*link){if(key<(*link)->value)link=&(*link)->left;else if(key>(*link)->value)link=&(*link)->right;else if(policy==DuplicatePolicy::left)link=&(*link)->left;else if(policy==DuplicatePolicy::right)link=&(*link)->right;else return std::nullopt;}*link=std::make_unique<Node>(key);}
    TreeBuildSummary result{{},-1};std::function<void(const Node*,int)>visit=[&](const Node* n,int depth){if(!n)return;visit(n->left.get(),depth+1);result.inorder.push_back(n->value);result.max_depth=std::max(result.max_depth,depth);visit(n->right.get(),depth+1);};visit(root.get(),0);return result;
}
