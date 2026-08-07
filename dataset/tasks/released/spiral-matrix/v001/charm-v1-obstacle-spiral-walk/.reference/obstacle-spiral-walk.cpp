#include <string>
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
