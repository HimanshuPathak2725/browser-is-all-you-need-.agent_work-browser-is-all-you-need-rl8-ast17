#include "clock.h"

#include <iomanip>
#include <sstream>

namespace date_independent {

namespace {
constexpr int minutes_per_hour = 60;
constexpr int minutes_per_day = 24 * minutes_per_hour;

int normalize_minutes(long long minutes)
{
    minutes %= minutes_per_day;
    if (minutes < 0) {
        minutes += minutes_per_day;
    }
    return static_cast<int>(minutes);
}
}  // namespace

clock::clock(int hour, int minute)
    : minutes_since_midnight(normalize_minutes(
          static_cast<long long>(hour) * minutes_per_hour + minute))
{
}

clock::clock(int minutes_since_midnight, bool)
    : minutes_since_midnight(normalize_minutes(minutes_since_midnight))
{
}

clock clock::at(int hour, int minute)
{
    return clock(hour, minute);
}

clock clock::add(int minutes) const
{
    return clock(
        normalize_minutes(static_cast<long long>(minutes_since_midnight) + minutes),
        true);
}

clock clock::subtract(int minutes) const
{
    return clock(
        normalize_minutes(static_cast<long long>(minutes_since_midnight) - minutes),
        true);
}

clock clock::plus(int minutes) const
{
    return add(minutes);
}

clock clock::minus(int minutes) const
{
    return subtract(minutes);
}

bool clock::operator==(const clock& other) const
{
    return minutes_since_midnight == other.minutes_since_midnight;
}

bool clock::operator!=(const clock& other) const
{
    return !(*this == other);
}

clock::operator std::string() const
{
    const int hour = minutes_since_midnight / minutes_per_hour;
    const int minute = minutes_since_midnight % minutes_per_hour;

    std::ostringstream result;
    result << std::setfill('0') << std::setw(2) << hour
           << ':'
           << std::setfill('0') << std::setw(2) << minute;

    return result.str();
}

}  // namespace date_independent
