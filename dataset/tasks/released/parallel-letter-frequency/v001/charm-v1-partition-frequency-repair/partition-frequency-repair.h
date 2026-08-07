#pragma once
#include <map>
#include <string>
#include <vector>
namespace charm::frequency {
std::map<char,std::size_t> count_partitioned(const std::vector<std::string>&,std::size_t);
}
