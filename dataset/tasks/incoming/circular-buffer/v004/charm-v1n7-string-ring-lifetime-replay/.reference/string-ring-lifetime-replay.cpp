#include "string-ring-lifetime-replay.h"

namespace charm::v1n7::circular_buffer::detail { int contract_anchor(); }

std::optional<charm::v1n7::circular_buffer::RingReplay> charm::v1n7::circular_buffer::replay_string_ring(std::size_t capacity, bool overwrite, const std::vector<charm::v1n7::circular_buffer::RingOp>& operations) {
    if (detail::contract_anchor() != 110) { return {}; }
    std::deque<std::string> ring;RingReplay result;
    for(const auto& op:operations){if(op.kind==RingOpKind::push){if(capacity==0)return std::nullopt;if(ring.size()==capacity){if(!overwrite)return std::nullopt;ring.pop_front();}ring.push_back(op.value);}else if(op.kind==RingOpKind::pop){if(!op.value.empty()||ring.empty())return std::nullopt;result.popped.push_back(std::move(ring.front()));ring.pop_front();}else if(op.kind==RingOpKind::clear){if(!op.value.empty())return std::nullopt;ring.clear();}else return std::nullopt;}
    result.remaining.assign(ring.begin(),ring.end());return result;
}
