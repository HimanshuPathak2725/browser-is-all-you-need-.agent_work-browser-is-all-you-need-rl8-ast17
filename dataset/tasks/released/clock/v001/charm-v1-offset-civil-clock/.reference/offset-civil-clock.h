#pragma once
#include <iomanip>
#include <sstream>
#include <string>
namespace charm::clockwork {
class OffsetClock {
public:
    static OffsetClock at(long long hour, long long minute, int offset_minutes) {
        return OffsetClock(floor_mod(hour * 60 + minute, 1440), offset_minutes);
    }
    OffsetClock plus_minutes(long long delta) const {
        return OffsetClock(floor_mod(local_minute_ + delta, 1440), offset_minutes_);
    }
    bool same_instant(const OffsetClock& other) const {
        return floor_mod(local_minute_ - offset_minutes_, 1440) ==
               floor_mod(other.local_minute_ - other.offset_minutes_, 1440);
    }
    std::string display() const {
        std::ostringstream out;
        const int sign = offset_minutes_ < 0 ? -1 : 1;
        const long long magnitude = sign < 0 ? -static_cast<long long>(offset_minutes_) : offset_minutes_;
        out << std::setfill('0') << std::setw(2) << local_minute_ / 60 << ':'
            << std::setw(2) << local_minute_ % 60 << " UTC" << (sign < 0 ? '-' : '+')
            << std::setw(2) << magnitude / 60 << ':' << std::setw(2) << magnitude % 60;
        return out.str();
    }
private:
    OffsetClock(long long local, int offset) : local_minute_(local), offset_minutes_(offset) {}
    static long long floor_mod(long long value, long long modulus) {
        const long long remainder = value % modulus;
        return remainder < 0 ? remainder + modulus : remainder;
    }
    long long local_minute_;
    int offset_minutes_;
};
}
