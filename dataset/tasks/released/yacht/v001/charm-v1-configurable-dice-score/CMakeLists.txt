cmake_minimum_required(VERSION 3.16)
project(charm_v1_configurable_dice_score LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
add_executable(task_test
    configurable-dice-score.cpp
    configurable-dice-score_test.cpp)
target_compile_options(task_test PRIVATE -Wall -Wextra -Werror -pedantic)
