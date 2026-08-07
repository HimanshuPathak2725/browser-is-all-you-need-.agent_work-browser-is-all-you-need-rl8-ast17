# Unique student roster

Review the supplied C++17 task in `unique-student-roster.h`, `unique-student-roster.cpp`. Build a roster from records with nonempty student IDs, grades 1 through 12, and scores 0 through 100. Student IDs must be unique. Return records ordered by ascending grade, descending score, then ID.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::grade_school {
struct StudentRecord { std::string id; int grade; int score; };
std::optional<std::vector<StudentRecord>> ordered_unique_roster(const std::vector<StudentRecord>& records);
}
```

Required edge behavior:

- header directly provides set
- student IDs are unique
- grade and score ranges are closed
- ordering has three keys
- empty roster is valid

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Preserve every byte of every editable file. Do not return file listings, fenced blocks, diffs, or replacements. If the supplied implementation satisfies the contract, return exactly `No changes are required.`
