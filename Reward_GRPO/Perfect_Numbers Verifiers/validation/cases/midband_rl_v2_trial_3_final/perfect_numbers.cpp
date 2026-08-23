#include "perfect_numbers.h"

#include <cstdint>
#include <stdexcept>

namespace perfect_numbers {

classification classify(int n) {
    if (n <= 0) {
        throw std::domain_error("Only positive integers are allowed");
    }
    if (n == 1) {
        return classification::deficient;
    }

    std::int64_t sum = 1;
    for (int divisor = 2;
         divisor <= n / divisor; ++divisor) {
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
