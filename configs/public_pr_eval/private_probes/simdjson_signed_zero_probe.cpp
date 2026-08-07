#include "simdjson.h"

#include <cmath>
#include <iostream>
#include <string>

namespace {

bool expect_dom(const char* text, bool negative_zero) {
  simdjson::dom::parser parser;
  simdjson::padded_string json{std::string(text)};
  double value = 1.0;
  const auto error = parser.parse(json).get(value);
  if (error || value != 0.0 || std::signbit(value) != negative_zero) {
    std::cerr << "DOM signed-zero mismatch\n";
    return false;
  }
  return true;
}

bool expect_ondemand(const char* text, bool negative_zero) {
  simdjson::ondemand::parser parser;
  simdjson::padded_string json{std::string(text)};
  auto document = parser.iterate(json);
  double value = 1.0;
  const auto error = document.get(value);
  if (error || value != 0.0 || std::signbit(value) != negative_zero) {
    std::cerr << "On-Demand signed-zero mismatch\n";
    return false;
  }
  return true;
}

}  // namespace

int main() {
  const char* negative_cases[] = {"-1e-999", "-0e-999", "-0.0e-999"};
  const char* positive_cases[] = {"1e-999", "0e-999", "0.0e-999"};
  for (const char* value : negative_cases) {
    if (!expect_dom(value, true) || !expect_ondemand(value, true)) return 1;
  }
  for (const char* value : positive_cases) {
    if (!expect_dom(value, false) || !expect_ondemand(value, false)) return 1;
  }
  return 0;
}
