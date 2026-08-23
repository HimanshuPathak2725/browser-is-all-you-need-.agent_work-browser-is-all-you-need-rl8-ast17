#include "perfect_numbers.h"

#include <cstdint>

namespace perfect_numbers {

classification classify(int n) {
    if (n <= 0) {
        throw std::domain_error("number must be positive");
    }

    std::int64_t sum = 1;
    for (int divisor = 2; divisor <= n / 2; ++divisor) {
        if (n % divisor == 0) {
            sum += divisor;
        }
    }

    if (sum == n) {
        return classification::perfect;
    }
    if (sum > n) {
        return classification::abundant;
    }
    return classification::deficient;
}

}  // namespace perfect_numbers
