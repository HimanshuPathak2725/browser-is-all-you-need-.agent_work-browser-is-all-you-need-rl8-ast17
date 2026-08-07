#pragma once
#include <algorithm>
#include <array>
#include <cctype>
#include <cstddef>
#include <string>
#include <thread>
#include <vector>
namespace charm::frequency {
inline std::array<std::size_t,26> count_bounded(const std::vector<std::string>& documents, std::size_t requested_workers) {
    std::array<std::size_t,26> total{};
    if (documents.empty() || requested_workers == 0) return total;
    const std::size_t workers = std::min(requested_workers, documents.size());
    std::vector<std::array<std::size_t,26>> local(workers);
    std::vector<std::thread> threads;
    for (std::size_t worker = 0; worker < workers; ++worker) {
        threads.emplace_back([&, worker] {
            for (std::size_t index = worker; index < documents.size(); index += workers)
                for (unsigned char ch : documents[index])
                    if (ch >= 'A' && ch <= 'Z') ++local[worker][ch - 'A'];
                    else if (ch >= 'a' && ch <= 'z') ++local[worker][ch - 'a'];
        });
    }
    for (auto& thread : threads) thread.join();
    for (const auto& counts : local) for (std::size_t i = 0; i < total.size(); ++i) total[i] += counts[i];
    return total;
}
}
