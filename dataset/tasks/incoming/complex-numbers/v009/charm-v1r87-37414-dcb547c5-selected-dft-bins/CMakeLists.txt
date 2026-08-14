cmake_minimum_required(VERSION 3.16)
project(charm_v1r87_37414_dcb547c5_selected_dft_bins LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
add_executable(task_test
    selected-dft-bins.cpp
    selected-dft-bins_detail.cpp
    selected-dft-bins_test.cpp)
target_compile_options(task_test PRIVATE -Wall -Wextra -Werror -pedantic -pthread)
target_link_libraries(task_test PRIVATE pthread)
