#if !defined(CLOCK_H)
#define CLOCK_H

#include <string>

namespace date_independent {

class clock {
public:
    clock(int hour, int minute);

    static clock at(int hour, int minute);

    clock add(int minutes) const;
    clock subtract(int minutes) const;

    clock plus(int minutes) const;
    clock minus(int minutes) const;

    bool operator==(const clock& other) const;
    bool operator!=(const clock& other) const;

    operator std::string() const;

private:
    explicit clock(int minutes_since_midnight, bool);

    int minutes_since_midnight;
};

}  // namespace date_independent

#endif  // CLOCK_H
