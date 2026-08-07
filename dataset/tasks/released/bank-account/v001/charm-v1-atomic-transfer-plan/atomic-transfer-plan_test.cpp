#include "atomic-transfer-plan.cpp"
#include <cassert>
#include <map>
#include <vector>
using charm::bank::AccountBook;
using charm::bank::Transfer;
int main() {
    AccountBook book({{"a", 10}, {"b", 0}, {"c", 0}});
    assert(book.execute({}) && book.balance_of("a") == 10);
    assert(book.execute({{"a", "b", 7}, {"b", "c", 7}}));
    assert(book.balance_of("a") == 3 && book.balance_of("b") == 0 && book.balance_of("c") == 7);
    assert(!book.execute({{"missing", "a", 1}}));
    assert(!book.execute({{"a", "c", -1}}));
    assert(!book.execute({{"a", "c", 4}}) && book.balance_of("a") == 3);
    assert(book.execute({{"a", "a", 3}}) && book.balance_of("a") == 3);
    assert(book.balance_of("unknown") == -1);
    return 0;
}
