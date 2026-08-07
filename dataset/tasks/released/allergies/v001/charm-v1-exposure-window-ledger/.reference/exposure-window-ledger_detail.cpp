namespace charm::allergy::detail {

bool within_inclusive_window(int minute, int now, int horizon) {
    const long long observed = minute;
    const long long upper = now;
    const long long lower = upper - static_cast<long long>(horizon);
    return observed >= lower && observed <= upper;
}

}  // namespace charm::allergy::detail
