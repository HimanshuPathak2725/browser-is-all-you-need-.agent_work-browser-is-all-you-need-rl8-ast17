# Conflict-aware transcript merge

Implement the C++17 task in `conflict-aware-transcript-merge.h`, `conflict-aware-transcript-merge.cpp`. Merge two transcript snapshots keyed by student ID. Identical records coalesce; a differing grade or score for the same ID is a conflict and rejects the merge. Records require valid IDs, grades, and scores. Return merged records ordered by ID.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::grade_school {
struct TranscriptRow { std::string id; int grade; int score; };
std::optional<std::vector<TranscriptRow>> merge_identical_transcripts(const std::vector<TranscriptRow>& left, const std::vector<TranscriptRow>& right);
}
```

Required edge behavior:

- identical duplicates coalesce
- conflicts reject
- validation covers both sides
- output is ID ordered
- empty inputs are valid

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
