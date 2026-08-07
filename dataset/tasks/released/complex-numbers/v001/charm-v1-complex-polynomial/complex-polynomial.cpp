#include <complex>
#include <vector>
namespace charm::complex {
struct PairValue { std::complex<double> value; std::complex<double> derivative; };
inline PairValue evaluate_with_derivative(
    const std::vector<std::complex<double>>& descending,
    std::complex<double> point) {
    PairValue result{{0.0, 0.0}, {0.0, 0.0}};
    for (const auto coefficient : descending) {
        result.derivative = result.derivative * point + coefficient;
        result.value = result.value * point + coefficient;
    }
    return result;
}
}
