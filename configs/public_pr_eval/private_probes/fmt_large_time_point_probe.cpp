#define FMT_HEADER_ONLY
#include "fmt/chrono.h"

#include <chrono>
#include <iostream>
#include <string>

namespace {

bool expect_date(long long epoch_seconds, const char* expected) {
  using milliseconds = std::chrono::milliseconds;
  using time_point = std::chrono::time_point<std::chrono::system_clock, milliseconds>;
  const time_point value{std::chrono::seconds(epoch_seconds)};
  const std::string actual = fmt::format("{:%Y-%m-%d}", value);
  if (actual == expected) return true;
  std::cerr << "date mismatch for epoch " << epoch_seconds << "\n";
  return false;
}

}  // namespace

int main() {
  if (!expect_date(0, "1970-01-01")) return 1;
  if (!expect_date(-2208988800LL, "1900-01-01")) return 1;
  if (!expect_date(16725225600LL, "2500-01-01")) return 1;
  if (!expect_date(32503680000LL, "3000-01-01")) return 1;
  return 0;
}
