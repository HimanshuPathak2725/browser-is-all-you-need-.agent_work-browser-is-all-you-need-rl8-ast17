#include "robot_name.h"

#include <algorithm>
#include <random>
#include <stdexcept>
#include <utility>
#include <vector>

namespace robot_name {

robot::robot() {
    reset();
}

std::string const& robot::name() const {
    return name_;
}

void robot::reset() {
    static std::vector<std::string> pool;
    static std::mt19937 engine{std::random_device{}()};
    static std::uniform_int_distribution<int> letters{'A', 'Z'};
    static std::uniform_int_distribution<int> digits{'0', '9'};

    if (pool.empty()) {
        for (int a = letters(engine); a <= letters(engine); ++a) {
            for (int b = letters(engine); b <= letters(engine); ++b) {
                for (int c = digits(engine); c <= digits(engine); ++c) {
                    for (int d = digits(engine); d <= digits(engine); ++d) {
                        for (int e = digits(engine); e <= digits(engine); ++e) {
                            pool.push_back(
                                std::string(1, static_cast<char>(a)) +
                                std::string(1, static_cast<char>(b)) +
                                std::string(1, static_cast<char>(c)) +
                                std::string(1, static_cast<char>(d)) +
                                std::string(1, static_cast<char>(e))
                            );
                        }
                    }
                }
            }
        }
        std::shuffle(pool.begin(), pool.end(), engine);
    }

    if (pool.empty()) {
        throw std::runtime_error("name space exhausted");
    }
    name_ = pool.back();
    pool.pop_back();
}

}  // namespace robot_name
