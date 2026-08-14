cmake_minimum_required(VERSION 3.16)
project(charm_v1r87_37414_dcb547c5_weekly_recurrence_wait LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
add_executable(task_test
    weekly-recurrence-wait.cpp
    weekly-recurrence-wait_detail.cpp
    weekly-recurrence-wait_test.cpp)
target_compile_options(task_test PRIVATE -Wall -Wextra -Werror -pedantic -pthread)
target_link_libraries(task_test PRIVATE pthread)
