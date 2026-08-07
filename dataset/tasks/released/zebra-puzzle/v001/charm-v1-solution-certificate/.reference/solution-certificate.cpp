#include <cmath>
#include <map>
#include <set>
#include <string>
#include <vector>
namespace charm::zebra {
enum class ClueKind { same_house, adjacent, immediately_left };
struct Clue { ClueKind kind; std::string a; std::string b; };
struct Verification { bool complete; std::vector<std::size_t> violated; };
inline Verification verify(int houses, const std::vector<std::vector<std::string>>& categories, const std::vector<Clue>& clues, const std::map<std::string,int>& assignment) {
    bool complete=houses>0; std::set<std::string> expected;
    for(const auto& category:categories){if(category.size()!=static_cast<std::size_t>(houses))complete=false;std::set<int> occupied;for(const auto& item:category){expected.insert(item);const auto found=assignment.find(item);if(found==assignment.end()||found->second<0||found->second>=houses||!occupied.insert(found->second).second)complete=false;}}
    if(assignment.size()!=expected.size())complete=false;
    std::vector<std::size_t> violated;
    for(std::size_t index=0;index<clues.size();++index){const auto a=assignment.find(clues[index].a),b=assignment.find(clues[index].b);bool pass=a!=assignment.end()&&b!=assignment.end();if(pass&&clues[index].kind==ClueKind::same_house)pass=a->second==b->second;if(pass&&clues[index].kind==ClueKind::adjacent)pass=std::abs(a->second-b->second)==1;if(pass&&clues[index].kind==ClueKind::immediately_left)pass=a->second+1==b->second;if(!pass)violated.push_back(index);}
    return {complete,violated};
}
}
