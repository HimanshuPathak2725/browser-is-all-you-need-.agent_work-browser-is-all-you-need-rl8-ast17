#include "perfect_numbers.h"

#include <cstdint>

namespace perfect_numbers {

classification classify(int n) {
    if (n <= 0) {
        throw std::domain_error("only positive integers can be classified");
    }

    if (n == 1) {
        return classification::deficient;
    }

    std::int64_t sum = 1; // 1 is always a proper divisor
    for (int divisor = 2; divisor <= n / divisor; ++divisor) {
        if (n % divisor == 0) {
            sum += divisor;
            const int other = n / divisor;
            if (other != divisor) {
                sum += other;
            }
        }
    }

    if (sum == n) {
        return classification::perfect;
    }
    return sum > n
        ? classification::abundant
        : classification::deficient;
}

}  // namespace perfect_numbers
