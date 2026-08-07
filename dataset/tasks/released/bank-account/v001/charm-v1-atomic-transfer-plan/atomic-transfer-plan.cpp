#include <map>
#include <string>
#include <string_view>
#include <vector>
namespace charm::bank {
struct Transfer { std::string from; std::string to; long long cents; };
class AccountBook {
public:
    explicit AccountBook(std::map<std::string, long long> balances) : balances_(balances) {}
    bool execute(const std::vector<Transfer>& plan);
    long long balance_of(std::string_view name) const;
private:
    std::map<std::string, long long> balances_;
};
}
