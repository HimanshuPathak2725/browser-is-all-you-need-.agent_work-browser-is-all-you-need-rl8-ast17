#include <string>
#include <vector>
namespace charm::bst {
class IntervalIndex {
public:
    bool add(int begin, int end, std::string label);
    std::vector<std::string> containing(int point) const;
};
}
