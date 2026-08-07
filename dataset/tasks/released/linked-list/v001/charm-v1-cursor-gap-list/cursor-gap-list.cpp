#include <cstddef>
#include <optional>
#include <vector>
namespace charm::list {
class GapList {
public:
    bool move(long long);
    void insert(int);
    std::optional<int> erase_next();
    std::vector<int> values() const;
    std::size_t cursor() const;
};
}
