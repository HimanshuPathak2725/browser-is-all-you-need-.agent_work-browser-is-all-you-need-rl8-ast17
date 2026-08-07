#pragma once
#include <complex>
#include <optional>
#include <utility>
#include <vector>
namespace charm::complex {
std::optional<double> weighted_direction(const std::vector<std::pair<std::complex<double>, double>>& phasors);
}
