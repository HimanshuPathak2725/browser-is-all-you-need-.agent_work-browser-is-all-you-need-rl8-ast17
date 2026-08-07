#pragma once
#include <algorithm>
#include <cstddef>
#include <map>
#include <string>
#include <vector>
namespace charm::frequency {
inline std::map<char,std::size_t> count_partitioned(const std::vector<std::string>& documents, std::size_t workers) {
    std::map<char,std::size_t> total;
    if (workers == 0 || documents.empty()) return total;
    const std::size_t actual = std::min(workers, documents.size());
    const std::size_t base = documents.size() / actual;
    const std::size_t remainder = documents.size() % actual;
    std::size_t begin = 0;
    for (std::size_t worker = 0; worker < actual; ++worker) {
        const std::size_t count = base + (worker < remainder ? 1 : 0);
        const std::size_t end = begin + count;
        for (std::size_t index = begin; index < end; ++index)
            for (unsigned char ch : documents[index]) {
                char key = 0;
                if (ch >= 'A' && ch <= 'Z') key = static_cast<char>(ch - 'A' + 'a');
                else if (ch >= 'a' && ch <= 'z') key = static_cast<char>(ch);
                if (key != 0) ++total[key];
            }
        begin = end;
    }
    return total;
}
}
