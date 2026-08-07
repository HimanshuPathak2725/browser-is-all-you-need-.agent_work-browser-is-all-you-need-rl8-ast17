#include "polar-mean-repair.hpp"
#include <cassert>
#include <cmath>
#include <complex>
#include <vector>
using charm::complex::weighted_direction;
int main() {
    assert(!weighted_direction({}));
    const auto east = weighted_direction({{{3, 0}, 2}});
    assert(east && std::abs(*east) < 1e-12);
    const auto north = weighted_direction({{{0, 2}, 5}, {{2, 0}, 0}});
    assert(north && std::abs(*north - std::acos(-1.0) / 2) < 1e-12);
    assert(!weighted_direction({{{1, 0}, 1}, {{-1, 0}, 1}}));
    assert(!weighted_direction({{{1, 0}, -1}}));
    const auto southwest = weighted_direction({{{-1, -1}, 2}});
    assert(southwest && *southwest > std::acos(-1.0));
    assert(!weighted_direction({{{0, 0}, 9}}));
    return 0;
}
