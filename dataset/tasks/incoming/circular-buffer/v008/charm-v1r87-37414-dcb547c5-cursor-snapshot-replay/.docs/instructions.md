# Cursor snapshot replay

Implement the C++17 task in `cursor-snapshot-replay.h`, `cursor-snapshot-replay.cpp`, `cursor-snapshot-replay_detail.cpp`. Replay a fixed-capacity integer ring with push-back, pop-front, save-cursor, and restore-cursor commands. Restore replaces the live ring with the named saved snapshot; malformed commands, unknown names, overflow, or underflow reject.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::circular_buffer {
struct RingCommand { std::string op; std::string name; int value; };
std::optional<std::vector<int>> replay_ring_snapshots(std::size_t capacity, const std::vector<RingCommand>& commands);
}
```

Required edge behavior:

- capacity zero permits only empty live rings
- snapshot names are nonempty and unique
- restore is non-destructive to the snapshot
- push/pop names are empty
- all invalid operations reject

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
