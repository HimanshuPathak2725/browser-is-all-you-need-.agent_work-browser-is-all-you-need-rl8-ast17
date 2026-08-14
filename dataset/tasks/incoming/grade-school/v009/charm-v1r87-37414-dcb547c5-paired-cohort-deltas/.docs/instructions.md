# Paired cohort deltas

Implement the C++17 task in `paired-cohort-deltas.h`, `paired-cohort-deltas.cpp`. Compare two named score maps that must contain exactly the same nonempty student set. Return improvement, equality, and decline counts plus the lower median signed delta after sorting.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::grade_school {
struct CohortDeltaSummary { std::size_t improved; std::size_t equal; std::size_t declined; int lower_median; };
std::optional<CohortDeltaSummary> summarize_paired_cohort_deltas(const std::map<std::string,int>& before, const std::map<std::string,int>& after);
}
```

Required edge behavior:

- cohorts are nonempty
- student key sets match exactly
- student names are nonempty
- deltas are checked
- even cohorts use the lower median

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
