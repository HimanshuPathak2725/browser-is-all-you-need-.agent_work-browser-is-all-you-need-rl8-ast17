"""Owner source for the three CHARM V1 Spiral Matrix tasks."""

from __future__ import annotations

from scripts.charm_v1_topics.common import calibration_prompt, package, prompt, support


FILL = r'''#pragma once
#include <cstddef>
#include <limits>
#include <vector>
namespace charm::spiral {
enum class Corner { top_left, top_right, bottom_right, bottom_left };
inline std::vector<std::vector<long long>> fill(std::size_t rows, std::size_t columns, Corner corner, long long start, long long step) {
    if (rows == 0 || columns == 0) return {};
    if (rows > static_cast<std::size_t>(std::numeric_limits<int>::max()) ||
        columns > static_cast<std::size_t>(std::numeric_limits<int>::max()) ||
        columns > std::numeric_limits<std::size_t>::max() / rows) {
        return {};
    }
    const std::size_t cell_count = rows * columns;
    std::vector<std::vector<long long>> matrix(rows, std::vector<long long>(columns));
    std::vector<std::vector<bool>> used(rows, std::vector<bool>(columns));
    const int dr[4]{0,1,0,-1}; const int dc[4]{1,0,-1,0};
    int row = 0, column = 0, direction = 0;
    if (corner == Corner::top_right) { column = static_cast<int>(columns)-1; direction = 1; }
    else if (corner == Corner::bottom_right) { row = static_cast<int>(rows)-1; column = static_cast<int>(columns)-1; direction = 2; }
    else if (corner == Corner::bottom_left) { row = static_cast<int>(rows)-1; direction = 3; }
    long long value = start;
    for (std::size_t count = 0; count < cell_count; ++count) {
        matrix[static_cast<std::size_t>(row)][static_cast<std::size_t>(column)] = value;
        used[static_cast<std::size_t>(row)][static_cast<std::size_t>(column)] = true;
        if (count + 1 < cell_count) {
            if (step > 0 && value > std::numeric_limits<long long>::max() - step)
                value = std::numeric_limits<long long>::max();
            else if (step < 0 && value < std::numeric_limits<long long>::min() - step)
                value = std::numeric_limits<long long>::min();
            else
                value += step;
        }
        int next_row = row + dr[direction], next_column = column + dc[direction];
        if (next_row < 0 || next_row >= static_cast<int>(rows) || next_column < 0 || next_column >= static_cast<int>(columns) || used[static_cast<std::size_t>(next_row)][static_cast<std::size_t>(next_column)]) {
            direction = (direction + 1) % 4;
            next_row = row + dr[direction]; next_column = column + dc[direction];
        }
        row = next_row; column = next_column;
    }
    return matrix;
}
}
'''
FILL_START = FILL.replace("direction = (direction + 1) % 4;", "direction = (direction + 3) % 4;")
FILL_TEST = r'''#include "rectangular-spiral-fill.h"
#include <cassert>
#include <limits>
#include <vector>
using charm::spiral::Corner;
using charm::spiral::fill;
int main() {
    assert(fill(0, 3, Corner::top_left, 1, 1).empty());
    assert((fill(1, 3, Corner::top_left, 5, 2) == std::vector<std::vector<long long>>{{5,7,9}}));
    assert((fill(2, 3, Corner::top_left, 1, 1) == std::vector<std::vector<long long>>{{1,2,3},{6,5,4}}));
    assert((fill(2, 3, Corner::top_right, 1, 1) == std::vector<std::vector<long long>>{{5,6,1},{4,3,2}}));
    assert((fill(2, 2, Corner::bottom_right, 10, -2) == std::vector<std::vector<long long>>{{6,4},{8,10}}));
    assert((fill(3, 1, Corner::bottom_left, 0, 3) == std::vector<std::vector<long long>>{{6},{3},{0}}));
    const auto repeat = fill(3, 4, Corner::bottom_right, -1, 0);
    for (const auto& row : repeat) for (long long value : row) assert(value == -1);
    const auto upper = fill(1, 2, Corner::top_left, std::numeric_limits<long long>::max(), 1);
    assert((upper == std::vector<std::vector<long long>>{{
        std::numeric_limits<long long>::max(), std::numeric_limits<long long>::max()}}));
    const auto lower = fill(1, 2, Corner::top_left, std::numeric_limits<long long>::min(), -1);
    assert((lower == std::vector<std::vector<long long>>{{
        std::numeric_limits<long long>::min(), std::numeric_limits<long long>::min()}}));
    return 0;
}
'''


WALK = r'''#include <string>
#include <vector>
namespace charm::spiral {
struct Cell { int row; int col; bool operator==(const Cell& other) const { return row == other.row && col == other.col; } };
inline std::vector<Cell> walk(const std::vector<std::string>& grid, Cell start) {
    if (grid.empty() || grid.front().empty()) return {};
    for (const auto& row : grid) if (row.size() != grid.front().size()) return {};
    const int rows = static_cast<int>(grid.size()), columns = static_cast<int>(grid.front().size());
    if (start.row < 0 || start.row >= rows || start.col < 0 || start.col >= columns || grid[start.row][start.col] != '.') return {};
    std::vector<std::vector<bool>> visited(grid.size(), std::vector<bool>(grid.front().size()));
    const int dr[4]{0,1,0,-1}; const int dc[4]{1,0,-1,0};
    int direction = 0; Cell current = start; std::vector<Cell> out;
    while (true) {
        out.push_back(current); visited[current.row][current.col] = true;
        bool moved = false;
        for (int turns = 0; turns < 4; ++turns) {
            const int nr = current.row + dr[direction], nc = current.col + dc[direction];
            if (nr >= 0 && nr < rows && nc >= 0 && nc < columns && grid[nr][nc] == '.' && !visited[nr][nc]) {
                current = {nr,nc}; moved = true; break;
            }
            direction = (direction + 1) % 4;
        }
        if (!moved) break;
    }
    return out;
}
}
'''
WALK_TEST = r'''#include "obstacle-spiral-walk.cpp"
#include <cassert>
#include <vector>
using charm::spiral::Cell;
using charm::spiral::walk;
int main() {
    assert(walk({}, {0,0}).empty());
    assert(walk({"..","."}, {0,0}).empty());
    assert(walk({"#"}, {0,0}).empty());
    assert((walk({"."}, {0,0}) == std::vector<Cell>{{0,0}}));
    assert((walk({"...","..."}, {0,0}) == std::vector<Cell>{{0,0},{0,1},{0,2},{1,2},{1,1},{1,0}}));
    assert((walk({"...",".#.","..."}, {0,0}) == std::vector<Cell>{{0,0},{0,1},{0,2},{1,2},{2,2},{2,1},{2,0},{1,0}}));
    assert(walk({".."}, {-1,0}).empty());
    return 0;
}
'''


LAYER = r'''#pragma once
#include <cstddef>
#include <vector>
namespace charm::spiral {
inline std::vector<int> layer_clockwise(const std::vector<std::vector<int>>& matrix, std::size_t layer) {
    if (matrix.empty() || matrix.front().empty()) return {};
    for (const auto& row : matrix) if (row.size() != matrix.front().size()) return {};
    const std::size_t top = layer, left = layer;
    if (top >= matrix.size() || left >= matrix.front().size()) return {};
    const std::size_t bottom = matrix.size() - 1 - layer;
    const std::size_t right = matrix.front().size() - 1 - layer;
    if (top > bottom || left > right) return {};
    std::vector<int> out;
    for (std::size_t column = left; column <= right; ++column) out.push_back(matrix[top][column]);
    for (std::size_t row = top + 1; row <= bottom; ++row) out.push_back(matrix[row][right]);
    if (bottom > top) for (std::size_t column = right; column-- > left;) out.push_back(matrix[bottom][column]);
    if (right > left) for (std::size_t row = bottom; row-- > top + 1;) out.push_back(matrix[row][left]);
    return out;
}
}
'''
LAYER_TEST = r'''#include "layer-view-repair.h"
#include <cassert>
#include <vector>
using charm::spiral::layer_clockwise;
int main() {
    assert(layer_clockwise({}, 0).empty());
    assert(layer_clockwise({{1,2},{3}}, 0).empty());
    assert((layer_clockwise({{1,2,3}}, 0) == std::vector<int>{1,2,3}));
    assert((layer_clockwise({{1},{2},{3}}, 0) == std::vector<int>{1,2,3}));
    const std::vector<std::vector<int>> matrix{{1,2,3,4},{5,6,7,8},{9,10,11,12},{13,14,15,16}};
    assert((layer_clockwise(matrix,0) == std::vector<int>{1,2,3,4,8,12,16,15,14,13,9,5}));
    assert((layer_clockwise(matrix,1) == std::vector<int>{6,7,11,10}));
    assert(layer_clockwise(matrix,2).empty());
    return 0;
}
'''


def tasks() -> list[dict]:
    fill_files = ["rectangular-spiral-fill.h", "rectangular-spiral-fill.cpp"]
    walk_files = ["obstacle-spiral-walk.cpp"]
    layer_files = ["layer-view-repair.h", "layer-view-repair.cpp"]
    layer_prompt = calibration_prompt("Rectangular layer view", "Extract a zero-based rectangular perimeter clockwise without duplicating corners or underflowing single-row and single-column layers.", "namespace charm::spiral { std::vector<int> layer_clockwise(const std::vector<std::vector<int>>&,std::size_t); }", ["empty and ragged matrices reject", "single row", "single column", "nested layer", "layer beyond the interior returns empty"], layer_files)
    rows = [
        package(topic="Spiral Matrix", task_id="charm-v1-rectangular-spiral-fill", instructions=prompt("Rectangular spiral fill", "Fill an arbitrary rectangular matrix clockwise from a selected corner, advancing by the caller's start value and step. Reject dimensions that cannot be safely indexed by returning empty. If an advance exceeds the long-long range, saturate that value and all later values at the reached limit.", "namespace charm::spiral { enum class Corner { top_left, top_right, bottom_right, bottom_left }; std::vector<std::vector<long long>> fill(std::size_t,std::size_t,Corner,long long,long long); }", ["zero or unindexable dimensions return empty", "one-row and one-column rectangles", "all four corners choose their clockwise initial direction", "negative or zero step", "long-long advancement saturates without signed overflow"], fill_files), editable={fill_files[0]: FILL_START, fill_files[1]: support(fill_files[0], 131)}, reference={fill_files[0]: FILL, fill_files[1]: support(fill_files[0], 132)}, hidden_name="rectangular-spiral-fill_test.cpp", hidden=FILL_TEST, category="corner-spiral", tags=["semantic-bug", "rectangular", "corner", "header-edit"]),
        package(topic="Spiral Matrix", task_id="charm-v1-obstacle-spiral-walk", instructions=prompt("Obstacle spiral walk", "Starting facing right, visit unblocked cells, turning clockwise whenever the next cell is blocked, outside, or visited; stop after no legal neighbor remains.", "namespace charm::spiral { struct Cell { int row; int col; bool operator==(const Cell&) const; }; std::vector<Cell> walk(const std::vector<std::string>&,Cell); }", ["grid is nonempty rectangular", "only dot cells are walkable", "invalid or blocked start returns empty", "a cell is never revisited", "the walk may stop before disconnected cells"], walk_files), editable={walk_files[0]: "#include <vector>\nnamespace charm::spiral { struct Cell { int row; int col; }; std::vector<Cell> walk(); }\n"}, reference={walk_files[0]: WALK}, hidden_name="obstacle-spiral-walk_test.cpp", hidden=WALK_TEST, category="obstacle-walk", tags=["api-repair", "turning", "visited", "cpp-only"]),
        package(topic="Spiral Matrix", task_id="charm-v1-layer-view-repair", instructions=layer_prompt, editable={layer_files[0]: LAYER, layer_files[1]: support(layer_files[0], 133)}, reference={layer_files[0]: LAYER, layer_files[1]: support(layer_files[0], 133)}, hidden_name="layer-view-repair_test.cpp", hidden=LAYER_TEST, category="perimeter-layer", tags=["calibration", "no-change", "thin-shape", "header-frozen"]),
    ]
    for row in rows:
        row["release_version"] = "v002"
    return rows
