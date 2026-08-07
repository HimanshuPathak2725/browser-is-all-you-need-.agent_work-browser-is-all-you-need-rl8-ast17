# Promotion cutline groups

Implement the C++17 task in `promotion-cutline-groups.cpp`. For each grade, promote the top requested count by score. A tie at the final promoted score expands the promoted set to include every tied student. Inputs require unique nonempty IDs, valid grades, valid scores, and valid requested grade keys. Return promoted IDs in lexical order.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::grade_school {
struct GradeScore { std::string id; int grade; int score; };
std::optional<std::vector<std::string>> promotion_cutline_ids(const std::vector<GradeScore>& scores, const std::map<int,std::size_t>& requested);
}
```

Required edge behavior:

- ties expand the cutline
- missing requests mean zero
- IDs are globally unique
- unknown grades reject
- output is lexical

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
