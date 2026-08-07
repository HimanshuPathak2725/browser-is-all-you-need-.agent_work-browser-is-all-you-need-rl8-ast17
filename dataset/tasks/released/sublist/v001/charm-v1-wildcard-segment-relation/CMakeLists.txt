cmake_minimum_required(VERSION 3.16)
project(charm_v1_wildcard_segment_relation LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
add_executable(task_test
    wildcard-segment-relation.cpp
    wildcard-segment-relation_test.cpp)
target_compile_options(task_test PRIVATE -Wall -Wextra -Werror -pedantic)
