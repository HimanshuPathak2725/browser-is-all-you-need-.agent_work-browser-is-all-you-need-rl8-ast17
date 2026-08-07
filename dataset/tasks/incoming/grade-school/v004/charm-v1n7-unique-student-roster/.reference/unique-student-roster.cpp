#include "unique-student-roster.h"

std::optional<std::vector<charm::v1n7::grade_school::StudentRecord>> charm::v1n7::grade_school::ordered_unique_roster(const std::vector<charm::v1n7::grade_school::StudentRecord>& records){std::set<std::string> ids;for(const auto& r:records)if(r.id.empty()||r.grade<1||r.grade>12||r.score<0||r.score>100||!ids.insert(r.id).second)return std::nullopt;auto out=records;std::sort(out.begin(),out.end(),[](const auto& a,const auto& b){if(a.grade!=b.grade)return a.grade<b.grade;if(a.score!=b.score)return a.score>b.score;return a.id<b.id;});return out;}
