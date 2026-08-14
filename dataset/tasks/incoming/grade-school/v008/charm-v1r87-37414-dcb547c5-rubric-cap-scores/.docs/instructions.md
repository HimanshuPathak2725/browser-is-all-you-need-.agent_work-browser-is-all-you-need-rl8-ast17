# Rubric cap scores

Review the supplied C++17 task in `rubric-cap-scores.h`, `rubric-cap-scores.cpp`. Score submissions against named positive rubric caps. Each submission supplies nonnegative criterion points, may omit criteria as zero, and may not name unknown criteria; cap each contribution and return totals by student.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::grade_school {
std::optional<std::map<std::string,std::int64_t>> score_capped_rubrics(const std::map<std::string,std::int64_t>& caps, const std::map<std::string,std::map<std::string,std::int64_t>>& submissions);
}
```

Required edge behavior:

- caps are named and positive
- students are named
- points are nonnegative
- unknown criteria reject
- each contribution is capped

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Preserve every byte of every editable file. Do not return file listings, fenced blocks, diffs, or replacements. If the supplied implementation satisfies the contract, return exactly `No changes are required.`
