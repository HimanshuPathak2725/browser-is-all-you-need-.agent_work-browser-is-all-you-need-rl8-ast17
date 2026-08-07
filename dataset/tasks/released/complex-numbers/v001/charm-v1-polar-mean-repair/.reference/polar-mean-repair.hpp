#pragma once
#include <cmath>
#include <complex>
#include <optional>
#include <utility>
#include <vector>
namespace charm::complex {
inline std::optional<double> weighted_direction(
    const std::vector<std::pair<std::complex<double>, double>>& phasors) {
    std::complex<long double> sum(0.0L, 0.0L);
    for (const auto& item : phasors) {
        const auto value = item.first;
        const double weight = item.second;
        if (weight < 0 || !std::isfinite(weight) || !std::isfinite(value.real()) || !std::isfinite(value.imag())) return std::nullopt;
        const double magnitude = std::abs(value);
        if (magnitude != 0.0 && weight != 0.0)
            sum += static_cast<long double>(weight) * std::complex<long double>(value.real() / magnitude, value.imag() / magnitude);
    }
    if (sum.real() == 0.0L && sum.imag() == 0.0L) return std::nullopt;
    long double angle = std::atan2(sum.imag(), sum.real());
    if (angle < 0) angle += 2.0L * std::acos(-1.0L);
    return static_cast<double>(angle);
}
}
