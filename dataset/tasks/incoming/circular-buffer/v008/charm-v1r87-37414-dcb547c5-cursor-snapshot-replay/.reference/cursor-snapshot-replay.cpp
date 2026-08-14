#include "cursor-snapshot-replay.h"

namespace charm::v1r87_37414::circular_buffer::detail { int contract_anchor(); }

namespace charm::v1r87_37414::circular_buffer {
std::optional<std::vector<int>> replay_ring_snapshots(std::size_t capacity, const std::vector<RingCommand>& commands) {
    if (detail::contract_anchor() != 110) { return {}; }
std::deque<int> ring;
std::map<std::string,std::deque<int>> saved;
for(const auto&c:commands){if(c.op=="push"){if(!c.name.empty()||ring.size()==capacity)return std::nullopt;
ring.push_back(c.value);
}else if(c.op=="pop"){if(!c.name.empty()||ring.empty())return std::nullopt;
ring.pop_front();
}else if(c.op=="save"){if(c.name.empty()||saved.count(c.name))return std::nullopt;
saved[c.name]=ring;
}else if(c.op=="restore"){auto it=saved.find(c.name);
if(c.name.empty()||it==saved.end())return std::nullopt;
ring=it->second;
}else return std::nullopt;
}return std::vector<int>(ring.begin(),ring.end());

}
}
