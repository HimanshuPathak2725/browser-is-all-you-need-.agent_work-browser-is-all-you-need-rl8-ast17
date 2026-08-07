#include "attendance-transaction-repair.h"
#include <cassert>
using charm::school::AttendanceBook;
int main() {
    AttendanceBook book;
    assert(!book.add_student("") && book.add_student("Ada") && book.add_student("Bob"));
    assert(!book.add_student("Ada"));
    assert(book.record_day({{"Ada",true},{"Bob",false}}));
    assert(book.totals("Ada") == std::make_pair(1,1));
    assert(book.totals("Bob") == std::make_pair(0,1));
    assert(!book.record_day({{"Ada",true},{"Ada",false}}));
    assert(book.totals("Ada") == std::make_pair(1,1));
    assert(!book.record_day({{"Ada",true},{"Eve",true}}));
    assert(!book.record_day({{"Ada",true}}));
    assert(book.totals("missing") == std::make_pair(-1,-1));
    return 0;
}
