#include "weighted-gradebook.cpp"
#include <cassert>
#include <optional>
#include <string>
#include <vector>
using charm::school::WeightedGradebook;
int main() {
    WeightedGradebook book;
    assert(!book.set("", "quiz", 90, 1) && !book.set("Ada", "", 90, 1));
    assert(!book.set("Ada", "quiz", 101, 1) && !book.set("Ada", "quiz", 90, 0));
    assert(book.set("Ada", "quiz", 80, 1) && book.set("Ada", "exam", 100, 3));
    assert(book.average_bp("Ada") == std::optional<int>(9500));
    assert(book.set("Ada", "quiz", 100, 1) && book.average_bp("Ada") == std::optional<int>(10000));
    assert(!book.average_bp("unknown"));
    assert(book.set("Bob", "one", 100, 1) && book.set("Amy", "one", 100, 1));
    assert((book.ranking() == std::vector<std::string>{"Ada", "Amy", "Bob"}));
    return 0;
}
