#pragma once
#include <algorithm>
#include <cmath>
#include <optional>
namespace charm::complex {
class StableComplex {
public:
    StableComplex(double real = 0.0, double imag = 0.0) : real_(real), imag_(imag) {}
    double real() const { return real_; }
    double imag() const { return imag_; }
    StableComplex operator+(StableComplex other) const { return {real_ + other.real_, imag_ + other.imag_}; }
    std::optional<StableComplex> divided_by(StableComplex divisor) const {
        if (!finite() || !divisor.finite() || (divisor.real_ == 0.0 && divisor.imag_ == 0.0)) return std::nullopt;
        double real = 0.0;
        double imag = 0.0;
        if (std::abs(divisor.real_) >= std::abs(divisor.imag_)) {
            const double ratio = divisor.imag_ / divisor.real_;
            const double denominator = divisor.real_ + divisor.imag_ * ratio;
            real = (real_ + imag_ * ratio) / denominator;
            imag = (imag_ - real_ * ratio) / denominator;
        } else {
            const double ratio = divisor.real_ / divisor.imag_;
            const double denominator = divisor.imag_ + divisor.real_ * ratio;
            real = (real_ * ratio + imag_) / denominator;
            imag = (imag_ * ratio - real_) / denominator;
        }
        if (!std::isfinite(real) || !std::isfinite(imag)) return std::nullopt;
        return StableComplex(real, imag);
    }
    bool near(StableComplex other, double absolute_tolerance, double relative_tolerance) const {
        if (!finite() || !other.finite() || absolute_tolerance < 0 || relative_tolerance < 0) return false;
        const double distance = std::hypot(real_ - other.real_, imag_ - other.imag_);
        const double scale = std::max(std::hypot(real_, imag_), std::hypot(other.real_, other.imag_));
        return distance <= absolute_tolerance + relative_tolerance * scale;
    }
private:
    bool finite() const { return std::isfinite(real_) && std::isfinite(imag_); }
    double real_;
    double imag_;
};
}
