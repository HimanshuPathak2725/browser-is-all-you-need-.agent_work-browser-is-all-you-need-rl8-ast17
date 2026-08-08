#define FMT_HEADER_ONLY
#include "fmt/chrono.h"

#include <chrono>
#include <cstdint>
#include <cstring>
#include <limits>
#include <string>
#include <type_traits>

namespace {

using fmt::detail::fmt_duration_cast;
using fmt::detail::is_same_arithmetic_type;

static_assert(is_same_arithmetic_type<int, long long>::value, "integral pair");
static_assert(is_same_arithmetic_type<float, double>::value, "floating pair");
static_assert(!is_same_arithmetic_type<int, double>::value, "mixed pair");

bool check_duration_cast() {
  const auto integral = fmt_duration_cast<std::chrono::milliseconds>(
      std::chrono::seconds(2));
  const auto floating = fmt_duration_cast<std::chrono::duration<double>>(
      std::chrono::duration<float>(1.5f));
  const auto mixed = fmt_duration_cast<std::chrono::milliseconds>(
      std::chrono::duration<double>(1.25));
  return integral.count() == 2000 && floating.count() == 1.5 &&
         mixed.count() == 1250;
}

bool check_to_time_t() {
  using point = std::chrono::time_point<std::chrono::system_clock,
                                        std::chrono::milliseconds>;
  const point future(std::chrono::seconds(32503680000LL));
  const point past(std::chrono::seconds(-2208988800LL));
  return fmt::detail::to_time_t(future) == std::time_t(32503680000LL) &&
         fmt::detail::to_time_t(past) == std::time_t(-2208988800LL);
}

bool check_gmtime() {
  using millis_point = std::chrono::time_point<std::chrono::system_clock,
                                               std::chrono::milliseconds>;
  using coarse = std::chrono::duration<long long, std::ratio<60>>;
  using coarse_point =
      std::chrono::time_point<std::chrono::system_clock, coarse>;
  const std::tm future = fmt::gmtime(millis_point(
      std::chrono::seconds(32503680000LL)));
  const std::tm epoch = fmt::gmtime(coarse_point(coarse(0)));
  return future.tm_year + 1900 == 3000 && epoch.tm_year + 1900 == 1970;
}

bool check_fractional() {
  return fmt::format("{:%S}", std::chrono::milliseconds(1234)) == "01.234" &&
         fmt::format("{:%S}", std::chrono::nanoseconds(-13420148734LL)) ==
             "-13.420148734";
}

bool check_milliseconds() {
  const auto positive =
      fmt::detail::get_milliseconds(std::chrono::milliseconds(1250));
  const auto negative =
      fmt::detail::get_milliseconds(std::chrono::milliseconds(-1250));
  return positive.count() == 250 && negative.count() == -250;
}

bool check_formatter() {
  using custom_int = std::chrono::duration<short, std::milli>;
  using custom_float = std::chrono::duration<float, std::milli>;
  return fmt::format("{:%S}", custom_int(1234)) == "01.234" &&
         fmt::format("{:%S}", custom_float(1500.0f)) == "01.500";
}

bool check_system_root() {
  using point = std::chrono::time_point<std::chrono::system_clock,
                                        std::chrono::milliseconds>;
  return fmt::format("{:%Y-%m-%d}",
                     point(std::chrono::seconds(32503680000LL))) ==
         "3000-01-01";
}

int check_local_root() {
#if FMT_USE_LOCAL_TIME
  using point = std::chrono::local_time<std::chrono::milliseconds>;
  const std::string value = fmt::format(
      "{:%Y-%m-%d %S}", point(std::chrono::milliseconds(1234)));
  return value == "1970-01-01 01.234" ? 0 : 1;
#else
  return 77;
#endif
}

int run(const char* id) {
  if (std::strcmp(id, "fmt-duration-cast-helper") == 0)
    return check_duration_cast() ? 0 : 1;
  if (std::strcmp(id, "same-arithmetic-dispatch") == 0) return 0;
  if (std::strcmp(id, "safe-cast-placement") == 0)
    return check_duration_cast() ? 0 : 1;
  if (std::strcmp(id, "to-time-t-helper") == 0)
    return check_to_time_t() ? 0 : 1;
  if (std::strcmp(id, "templated-gmtime") == 0)
    return check_gmtime() ? 0 : 1;
  if (std::strcmp(id, "localtime-to-time-t") == 0)
    return check_local_root();
  if (std::strcmp(id, "fractional-seconds-casts") == 0)
    return check_fractional() ? 0 : 1;
  if (std::strcmp(id, "remove-old-safe-helper") == 0) return 0;
  if (std::strcmp(id, "milliseconds-casts") == 0)
    return check_milliseconds() ? 0 : 1;
  if (std::strcmp(id, "chrono-formatter-cast") == 0)
    return check_formatter() ? 0 : 1;
  if (std::strcmp(id, "time-point-root-fix") == 0)
    return check_system_root() ? 0 : 1;
  if (std::strcmp(id, "local-time-root-fix") == 0)
    return check_local_root();
  if (std::strcmp(id, "all-nonlocal") == 0)
    return check_duration_cast() && check_to_time_t() && check_gmtime() &&
                   check_fractional() && check_milliseconds() &&
                   check_formatter() && check_system_root()
               ? 0
               : 1;
  return 64;
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 2) return 64;
  return run(argv[1]);
}
