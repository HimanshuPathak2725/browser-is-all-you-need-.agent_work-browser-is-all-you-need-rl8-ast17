#include <catch2/catch_test_macros.hpp>

#include <stdexcept>

TEST_CASE("checked-else true does not hide a later exception", "[!shouldfail]") {
  CHECKED_ELSE(true) {}
  throw std::runtime_error("later exception");
}

TEST_CASE("checked-else false does not hide a later exception", "[!shouldfail]") {
  CHECKED_ELSE(false) {}
  throw std::runtime_error("later exception");
}
