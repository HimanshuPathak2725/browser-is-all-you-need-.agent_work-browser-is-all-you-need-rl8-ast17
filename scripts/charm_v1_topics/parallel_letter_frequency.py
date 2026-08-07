"""Owner source for the three CHARM V1 Parallel Letter Frequency tasks."""

from __future__ import annotations

from scripts.charm_v1_topics.common import package, prompt, support


BOUNDED = r'''#pragma once
#include <algorithm>
#include <array>
#include <atomic>
#include <cstddef>
#include <string>
#include <thread>
#include <vector>
namespace charm::frequency {
inline std::array<std::size_t,26> count_bounded(const std::vector<std::string>& documents, std::size_t requested_workers) {
    std::array<std::size_t,26> total{};
    if (documents.empty() || requested_workers == 0) return total;
    const std::size_t workers = std::min(requested_workers, documents.size());
    std::atomic<std::size_t> next_document{0};
    std::vector<std::array<std::size_t,26>> local(workers);
    std::vector<std::thread> threads;
    threads.reserve(workers);
    for (std::size_t worker = 0; worker < workers; ++worker) {
        threads.emplace_back([&, worker] {
            while (true) {
                const std::size_t index = next_document.fetch_add(1, std::memory_order_relaxed);
                if (index >= documents.size()) break;
                for (unsigned char ch : documents[index])
                    if (ch >= 'A' && ch <= 'Z') ++local[worker][ch - 'A'];
                    else if (ch >= 'a' && ch <= 'z') ++local[worker][ch - 'a'];
            }
        });
    }
    for (auto& thread : threads) thread.join();
    for (const auto& counts : local) for (std::size_t i = 0; i < total.size(); ++i) total[i] += counts[i];
    return total;
}
}
'''
BOUNDED_TEST = r'''#include "bounded-shard-frequency.h"
#include <cassert>
#include <vector>
using charm::frequency::count_bounded;
int main() {
    const auto empty = count_bounded({}, 4); assert(empty[0] == 0);
    const auto zero = count_bounded({"abc"}, 0); assert(zero[0] == 0);
    const auto one = count_bounded({"Aa! z", "bA", "123"}, 1);
    assert(one[0] == 3 && one[1] == 1 && one[25] == 1);
    const auto many = count_bounded({"Aa! z", "bA", "123"}, 99);
    assert(many == one);
    const auto mixed = count_bounded({"XYZ", "xyz", "x"}, 2);
    assert(mixed[23] == 3 && mixed[24] == 2 && mixed[25] == 2);
    const auto repeat = count_bounded({"parallel", "letter"}, 2);
    assert(repeat == count_bounded({"parallel", "letter"}, 2));
    return 0;
}
'''


MERGE = r'''#include <array>
#include <cstddef>
#include <limits>
#include <mutex>
#include <set>
#include <string>
namespace charm::frequency {
class MergeCounter {
public:
    bool merge(std::string shard, const std::array<std::size_t,26>& values) {
        std::lock_guard<std::mutex> lock(mutex_);
        if (shard.empty() || merged_.count(shard) != 0U) return false;
        for (std::size_t i = 0; i < counts_.size(); ++i)
            if (values[i] > std::numeric_limits<std::size_t>::max() - counts_[i]) return false;
        merged_.insert(std::move(shard));
        for (std::size_t i = 0; i < counts_.size(); ++i) counts_[i] += values[i];
        return true;
    }
    std::size_t count(char letter) const {
        std::lock_guard<std::mutex> lock(mutex_);
        const unsigned char ch = static_cast<unsigned char>(letter);
        if (ch >= 'A' && ch <= 'Z') return counts_[ch - 'A'];
        if (ch >= 'a' && ch <= 'z') return counts_[ch - 'a'];
        return 0;
    }
    std::size_t merged_shards() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return merged_.size();
    }
private:
    mutable std::mutex mutex_;
    std::array<std::size_t,26> counts_{};
    std::set<std::string> merged_;
};
}
'''
MERGE_START = MERGE.replace("if (shard.empty() || merged_.count(shard) != 0U) return false;", "if (shard.empty()) return false;")
MERGE_TEST = r'''#include "mergeable-frequency.cpp"
#include <array>
#include <atomic>
#include <cassert>
#include <limits>
#include <string>
#include <thread>
#include <vector>
using charm::frequency::MergeCounter;
int main() {
    MergeCounter counter;
    std::array<std::size_t,26> one{}; one[0]=2; one[25]=1;
    assert(!counter.merge("", one));
    assert(counter.merge("s1", one) && counter.merged_shards() == 1);
    assert(counter.count('a') == 2 && counter.count('A') == 2 && counter.count('z') == 1);
    assert(!counter.merge("s1", one) && counter.count('a') == 2);
    std::array<std::size_t,26> two{}; two[0]=3;
    assert(counter.merge("s2", two) && counter.count('a') == 5);
    assert(counter.count('?') == 0);
    std::array<std::size_t,26> huge{}; huge[0]=std::numeric_limits<std::size_t>::max();
    assert(!counter.merge("overflow", huge) && counter.merged_shards() == 2);
    std::array<std::size_t,26> b{}; b[1]=1;
    std::atomic<int> wins{0};
    std::vector<std::thread> threads;
    for (int index=0; index<8; ++index) threads.emplace_back([&] { if(counter.merge("same", b)) ++wins; });
    for (auto& thread : threads) thread.join();
    assert(wins == 1 && counter.count('b') == 1 && counter.merged_shards() == 3);
    threads.clear();
    for (int index=0; index<8; ++index) threads.emplace_back([&,index] { assert(counter.merge("unique-" + std::to_string(index), b)); });
    for (auto& thread : threads) thread.join();
    assert(counter.count('b') == 9 && counter.merged_shards() == 11);
    return 0;
}
'''


PARTITIONED = r'''#pragma once
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
'''
PARTITIONED_START = r'''#pragma once
#include <map>
#include <string>
#include <vector>
namespace charm::frequency {
std::map<char,std::size_t> count_partitioned(const std::vector<std::string>&,std::size_t);
}
'''
PARTITIONED_TEST = r'''#include "partition-frequency-repair.h"
#include <cassert>
#include <map>
#include <vector>
using charm::frequency::count_partitioned;
int main() {
    assert(count_partitioned({}, 3).empty());
    assert(count_partitioned({"abc"}, 0).empty());
    const std::vector<std::string> docs{"Aa", "b!", "CcC", ""};
    const auto expected = std::map<char,std::size_t>{{'a',2},{'b',1},{'c',3}};
    assert(count_partitioned(docs, 1) == expected);
    assert(count_partitioned(docs, 2) == expected);
    assert(count_partitioned(docs, 99) == expected);
    assert(count_partitioned({"X", "y", "Z"}, 2).size() == 3);
    assert(count_partitioned(docs, 3) == count_partitioned(docs, 3));
    return 0;
}
'''


def tasks() -> list[dict]:
    bounded = ["bounded-shard-frequency.h", "bounded-shard-frequency.cpp"]
    merge = ["mergeable-frequency.cpp"]
    partitioned = ["partition-frequency-repair.h", "partition-frequency-repair.cpp"]
    return [
        package(topic="Parallel Letter Frequency", task_id="charm-v1-bounded-shard-frequency", instructions=prompt("Bounded shard frequency", "Count ASCII letters case-insensitively across documents with no more than the requested worker count and merge deterministic local arrays.", "namespace charm::frequency { std::array<std::size_t,26> count_bounded(const std::vector<std::string>&,std::size_t); }", ["zero workers returns zero counts", "empty input", "workers may exceed documents", "non-ASCII-letter bytes are ignored", "results are independent of worker count"], bounded), editable={bounded[0]: "#pragma once\nnamespace charm::frequency {}\n", bounded[1]: support(bounded[0], 111)}, reference={bounded[0]: BOUNDED, bounded[1]: support(bounded[0], 112)}, hidden_name="bounded-shard-frequency_test.cpp", hidden=BOUNDED_TEST, category="bounded-parallelism", tags=["threads", "determinism", "ascii", "header-extension"]),
        package(topic="Parallel Letter Frequency", task_id="charm-v1-mergeable-frequency", instructions=prompt("Mergeable frequency", "Merge each identified 26-letter count shard at most once, atomically rejecting duplicate IDs or size_t overflow.", "namespace charm::frequency { class MergeCounter { public: bool merge(std::string,const std::array<std::size_t,26>&); std::size_t count(char) const; std::size_t merged_shards() const; }; }", ["empty shard ID rejects", "duplicate shard is inert", "overflow rejects the whole shard", "queries are ASCII case-insensitive", "nonletters report zero"], merge), editable={merge[0]: MERGE_START}, reference={merge[0]: MERGE}, hidden_name="mergeable-frequency_test.cpp", hidden=MERGE_TEST, category="idempotent-merge", tags=["semantic-bug", "atomicity", "overflow", "cpp-only"]),
        package(topic="Parallel Letter Frequency", task_id="charm-v1-partition-frequency-repair", instructions=prompt("Partitioned frequency repair", "Partition documents into deterministic contiguous chunks so every document is counted exactly once, including when workers exceed inputs.", "namespace charm::frequency { std::map<char,std::size_t> count_partitioned(const std::vector<std::string>&,std::size_t); }", ["zero workers", "empty documents", "empty chunks are not created", "remainder documents distribute to early chunks", "ASCII normalization is deterministic"], partitioned), editable={partitioned[0]: PARTITIONED_START, partitioned[1]: support(partitioned[0], 113)}, reference={partitioned[0]: PARTITIONED, partitioned[1]: support(partitioned[0], 114)}, hidden_name="partition-frequency-repair_test.cpp", hidden=PARTITIONED_TEST, category="deterministic-partition", tags=["repair", "partitioning", "coverage", "header-edit"]),
    ]
