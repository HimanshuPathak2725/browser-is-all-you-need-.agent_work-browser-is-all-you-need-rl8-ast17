#pragma once
#include <cstddef>
#include <vector>
namespace charm::spiral {
enum class Corner { top_left, top_right, bottom_right, bottom_left };
inline std::vector<std::vector<long long>> fill(std::size_t rows, std::size_t columns, Corner corner, long long start, long long step) {
    if (rows == 0 || columns == 0) return {};
    std::vector<std::vector<long long>> matrix(rows, std::vector<long long>(columns));
    std::vector<std::vector<bool>> used(rows, std::vector<bool>(columns));
    const int dr[4]{0,1,0,-1}; const int dc[4]{1,0,-1,0};
    int row = 0, column = 0, direction = 0;
    if (corner == Corner::top_right) { column = static_cast<int>(columns)-1; direction = 1; }
    else if (corner == Corner::bottom_right) { row = static_cast<int>(rows)-1; column = static_cast<int>(columns)-1; direction = 2; }
    else if (corner == Corner::bottom_left) { row = static_cast<int>(rows)-1; direction = 3; }
    long long value = start;
    for (std::size_t count = 0; count < rows * columns; ++count) {
        matrix[static_cast<std::size_t>(row)][static_cast<std::size_t>(column)] = value;
        used[static_cast<std::size_t>(row)][static_cast<std::size_t>(column)] = true;
        value += step;
        int next_row = row + dr[direction], next_column = column + dc[direction];
        if (next_row < 0 || next_row >= static_cast<int>(rows) || next_column < 0 || next_column >= static_cast<int>(columns) || used[static_cast<std::size_t>(next_row)][static_cast<std::size_t>(next_column)]) {
            direction = (direction + 3) % 4;
            next_row = row + dr[direction]; next_column = column + dc[direction];
        }
        row = next_row; column = next_column;
    }
    return matrix;
}
}
