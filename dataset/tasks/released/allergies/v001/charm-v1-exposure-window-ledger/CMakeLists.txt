cmake_minimum_required(VERSION 3.16)
project(charm_v1_exposure_window_ledger LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
add_executable(exposure_window_ledger_test
    exposure-window-ledger.cpp
    exposure-window-ledger_detail.cpp
    exposure-window-ledger_test.cpp)
target_compile_options(exposure_window_ledger_test PRIVATE -Wall -Wextra -Werror -pedantic)
