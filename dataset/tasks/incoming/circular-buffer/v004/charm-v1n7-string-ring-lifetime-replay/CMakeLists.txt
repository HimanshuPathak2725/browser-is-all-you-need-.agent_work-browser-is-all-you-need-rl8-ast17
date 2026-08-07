cmake_minimum_required(VERSION 3.16)
project(charm_v1n7_string_ring_lifetime_replay LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
add_executable(task_test
    string-ring-lifetime-replay.cpp
    string-ring-lifetime-replay_detail.cpp
    string-ring-lifetime-replay_test.cpp)
target_compile_options(task_test PRIVATE -Wall -Wextra -Werror -pedantic -pthread)
target_link_libraries(task_test PRIVATE pthread)
