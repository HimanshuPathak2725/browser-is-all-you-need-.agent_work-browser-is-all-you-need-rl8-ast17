"""Clock task definitions for the four-topic 60-task batch."""

from __future__ import annotations

from .common import TaskSpec


SPECS = (
    TaskSpec(
        "pulse-coincidence-crt",
        r"""
namespace pulse_coincidence {
static std::int64_t mod(std::int64_t x, std::int64_t m) {
    const auto r = x % m;
    return r < 0 ? r + m : r;
}
static std::int64_t egcd(std::int64_t a, std::int64_t b, std::int64_t& x, std::int64_t& y) {
    if (b == 0) { x = 1; y = 0; return a; }
    std::int64_t x1 = 0, y1 = 0;
    const auto g = egcd(b, a % b, x1, y1);
    x = y1;
    y = x1 - (a / b) * y1;
    return g;
}
std::optional<std::int64_t> first_alignment(
    std::int64_t ap, std::int64_t av, std::int64_t bp, std::int64_t bv,
    std::int64_t limit) {
    if (ap <= 0 || bp <= 0 || limit < 0) throw std::invalid_argument("period");
    av = mod(av, ap); bv = mod(bv, bp);
    std::int64_t x = 0, y = 0;
    const auto g = egcd(ap, bp, x, y);
    const auto difference = bv - av;
    if (difference % g != 0) return std::nullopt;
    const auto reduced = bp / g;
    const auto factor = mod((difference / g) * x, reduced);
    if (factor != 0 && ap > (std::numeric_limits<std::int64_t>::max() - av) / factor) {
        throw std::overflow_error("alignment");
    }
    const auto answer = av + ap * factor;
    if (answer <= limit) return answer;
    return std::nullopt;
}
}
""",
        r"""
int main() {
    using pulse_coincidence::first_alignment;
    assert(first_alignment(4, 1, 6, 3, 20) == 9);
    assert(first_alignment(4, 1, 6, 2, 20) == std::nullopt);
    assert(first_alignment(5, -1, 7, 3, 40) == 24);
    assert(first_alignment(3, 0, 5, 0, 0) == 0);
    assert(first_alignment(4, 1, 6, 3, 9) == 9);
    assert(first_alignment(4, 1, 6, 3, 8) == std::nullopt);
    bool bad = false; try { (void)first_alignment(0,0,1,0,1); } catch (const std::invalid_argument&) { bad = true; }
    assert(bad);
}
""",
        "if (answer <= limit)",
        "if (answer < limit)",
        "generalized-crt",
        ("congruence", "gcd", "checked-arithmetic"),
    ),
    TaskSpec(
        "tariff-band-shift-split",
        r"""
namespace tariff_clock {
std::vector<std::int64_t> split_cost(
    int start, int duration, const std::vector<Band>& bands) {
    if (start < 0 || start >= 1440 || duration < 0 || bands.empty()) {
        throw std::invalid_argument("shift");
    }
    int cursor = 0;
    for (const auto& band : bands) {
        if (band.begin_minute != cursor || band.end_minute <= band.begin_minute ||
            band.end_minute > 1440 || band.rate < 0) throw std::invalid_argument("bands");
        cursor = band.end_minute;
    }
    if (cursor != 1440) throw std::invalid_argument("partition");
    std::vector<std::int64_t> result(bands.size(), 0);
    std::int64_t absolute = start;
    std::int64_t remaining = duration;
    while (remaining > 0) {
        const int minute = static_cast<int>(absolute % 1440);
        std::size_t index = 0;
        while (minute >= bands[index].end_minute) ++index;
        const auto available = static_cast<std::int64_t>(bands[index].end_minute - minute);
        const auto take = std::min(remaining, available);
        result[index] += take * bands[index].rate;
        absolute += take;
        remaining -= take;
    }
    return result;
}
}
""",
        r"""
int main() {
    using tariff_clock::Band; using tariff_clock::split_cost;
    const std::vector<Band> bands{{0,480,1},{480,1020,2},{1020,1440,3}};
    assert((split_cost(0,60,bands) == std::vector<std::int64_t>{60,0,0}));
    assert((split_cost(470,20,bands) == std::vector<std::int64_t>{10,20,0}));
    assert((split_cost(1430,20,bands) == std::vector<std::int64_t>{10,0,30}));
    assert((split_cost(0,2880,bands) == std::vector<std::int64_t>{960,2160,2520}));
    assert((split_cost(100,0,bands) == std::vector<std::int64_t>{0,0,0}));
    bool bad=false; try { (void)split_cost(0,1,{{0,100,1}}); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "result[index] += take * bands[index].rate;",
        "result[index] += take;",
        "daily-band-sweep",
        ("tariff", "boundary-sweep", "multi-day"),
    ),
    TaskSpec(
        "pauseable-countdown-ledger",
        r"""
namespace countdown_ledger {
std::int64_t remaining(std::int64_t initial, const std::vector<Op>& ops) {
    if (initial < 0) throw std::invalid_argument("initial");
    bool running = true;
    std::int64_t left = initial;
    for (const auto& op : ops) {
        if (op.kind == OpKind::advance) {
            if (op.amount < 0) throw std::invalid_argument("advance");
            if (running) left = op.amount >= left ? 0 : left - op.amount;
        } else if (op.kind == OpKind::pause) {
            if (!running || op.amount != 0) throw std::logic_error("pause");
            running = false;
        } else {
            if (running || op.amount != 0) throw std::logic_error("resume");
            running = true;
        }
    }
    return left;
}
}
""",
        r"""
int main() {
    using namespace countdown_ledger;
    assert(remaining(10,{{OpKind::advance,3}})==7);
    assert(remaining(10,{{OpKind::pause,0},{OpKind::advance,9},{OpKind::resume,0},{OpKind::advance,4}})==6);
    assert(remaining(2,{{OpKind::advance,8}})==0);
    assert(remaining(0,{})==0);
    bool bad=false; try { (void)remaining(3,{{OpKind::pause,0},{OpKind::pause,0}}); } catch(const std::logic_error&) { bad=true; }
    assert(bad);
    bad=false; try { (void)remaining(-1,{}); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "bool running = true;",
        "bool running = false;",
        "countdown-state-machine",
        ("pause", "resume", "saturating-time"),
    ),
    TaskSpec(
        "ntp-sample-consensus",
        r"""
namespace ntp_consensus {
std::optional<Estimate> estimate(const std::vector<Sample>& samples) {
    std::vector<Estimate> valid;
    for (const auto& s : samples) {
        if (s.t1 > s.t2 || s.t2 > s.t3 || s.t3 > s.t4) continue;
        const auto delay = (s.t4 - s.t1) - (s.t3 - s.t2);
        if (delay < 0) continue;
        const double offset = (static_cast<double>(s.t2 - s.t1) +
                               static_cast<double>(s.t3 - s.t4)) / 2.0;
        valid.push_back({offset, delay});
    }
    if (valid.empty()) return std::nullopt;
    std::sort(valid.begin(), valid.end(), [](const Estimate& a, const Estimate& b) {
        return std::tie(a.delay, a.offset) < std::tie(b.delay, b.offset);
    });
    const std::size_t selected_count = (valid.size() + 3) / 4;
    valid.resize(selected_count);
    std::vector<double> offsets;
    for (const auto& item : valid) offsets.push_back(item.offset);
    std::sort(offsets.begin(), offsets.end());
    const auto middle = offsets.size() / 2;
    const double median = offsets.size() % 2 ? offsets[middle]
        : (offsets[middle - 1] + offsets[middle]) / 2.0;
    return Estimate{median, valid[middle].delay};
}
}
""",
        r"""
int main() {
    using namespace ntp_consensus;
    assert(!estimate({}));
    const auto one=estimate({{0,4,6,10}});
    assert(one && one->delay==8 && std::abs(one->offset)<1e-12);
    assert(!estimate({{5,4,7,8}}));
    const auto many=estimate({{0,1,2,3},{0,2,3,6},{0,10,11,30},{0,20,21,50}});
    assert(many && many->delay==2);
    const auto even=estimate({{0,2,3,5},{0,4,5,9},{0,20,21,41},{0,30,31,61},
                              {0,6,7,13},{0,8,9,17},{0,40,41,81},{0,50,51,101}});
    assert(even && std::isfinite(even->offset));
}
""",
        "const std::size_t selected_count = (valid.size() + 3) / 4;",
        "const std::size_t selected_count = valid.size();",
        "ntp-quartile-consensus",
        ("ntp", "minimum-delay-quartile", "median"),
    ),
    TaskSpec(
        "metronome-rational-merge",
        r"""
namespace metronome_merge {
static std::pair<std::int64_t,std::int64_t> reduce(std::int64_t n, std::int64_t d) {
    const auto g = std::gcd(n < 0 ? -n : n, d < 0 ? -d : d);
    n /= g; d /= g;
    if (d < 0) { n = -n; d = -d; }
    return {n,d};
}
std::vector<Beat> merge(
    std::int64_t hn, std::int64_t hd,
    const std::vector<std::pair<std::int64_t,std::int64_t>>& periods) {
    if (hd <= 0 || hn < 0) throw std::invalid_argument("horizon");
    const auto horizon = reduce(hn, hd);
    using Rational=std::pair<std::int64_t,std::int64_t>;
    std::map<Rational, int,
             std::function<bool(const Rational&,const Rational&)>> beats(
        [](const Rational& a,const Rational& b) {
            return static_cast<long double>(a.first)*b.second <
                   static_cast<long double>(b.first)*a.second;
        });
    for (std::size_t source=0; source<periods.size(); ++source) {
        auto period=reduce(periods[source].first, periods[source].second);
        if (period.first <= 0) throw std::invalid_argument("period");
        for (std::int64_t k=0;;++k) {
            if (k > std::numeric_limits<std::int64_t>::max()/period.first) break;
            auto value=reduce(k*period.first,period.second);
            if (static_cast<long double>(value.first)*horizon.second >
                static_cast<long double>(horizon.first)*value.second) break;
            auto found=beats.find(value);
            if (found==beats.end()) beats.emplace(value,static_cast<int>(source));
            else found->second=std::min(found->second,static_cast<int>(source));
        }
    }
    std::vector<Beat> out;
    for (const auto& [value,source]:beats) out.push_back({value.first,value.second,source});
    return out;
}
}
""",
        r"""
int main() {
    using metronome_merge::merge;
    auto a=merge(2,1,{{1,1}});
    assert(a.size()==3 && a[0].numerator==0 && a[2].numerator==2);
    auto b=merge(3,2,{{1,2},{2,4}});
    assert(b.size()==4);
    assert(b[1].numerator==1 && b[1].denominator==2 && b[1].source==0);
    assert(merge(0,1,{{3,2}}).size()==1);
    bool bad=false; try { (void)merge(1,1,{{0,1}}); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "for (std::int64_t k=0;;++k)",
        "for (std::int64_t k=1;;++k)",
        "rational-event-merge",
        ("rational", "coalescing", "gcd-normalization"),
    ),
    TaskSpec(
        "itinerary-utc-monotonicity",
        r"""
namespace itinerary_clock {
std::optional<std::int64_t> minimum_layover(const std::vector<Leg>& legs) {
    if (legs.size() < 2) return std::nullopt;
    std::optional<std::int64_t> best;
    std::int64_t previous_arrival = 0;
    for (std::size_t i=0;i<legs.size();++i) {
        const auto departure=legs[i].local_departure-legs[i].departure_offset;
        const auto arrival=legs[i].local_arrival-legs[i].arrival_offset;
        if (arrival < departure) return std::nullopt;
        if (i>0) {
            if (departure < previous_arrival) return std::nullopt;
            const auto gap=departure-previous_arrival;
            if (!best || gap<*best) best=gap;
        }
        previous_arrival=arrival;
    }
    return best;
}
}
""",
        r"""
int main() {
    using itinerary_clock::Leg; using itinerary_clock::minimum_layover;
    assert(!minimum_layover({}));
    assert(!minimum_layover({{0,0,10,0}}));
    assert(minimum_layover({{100,60,200,60},{240,60,300,60}})==40);
    assert(minimum_layover({{100,120,150,120},{90,60,120,60}})==0);
    assert(!minimum_layover({{0,0,10,0},{9,0,20,0}}));
    assert(!minimum_layover({{10,0,0,0},{20,0,30,0}}));
}
""",
        "if (departure < previous_arrival)",
        "if (departure <= previous_arrival)",
        "utc-itinerary-validation",
        ("utc-offset", "layover", "monotonicity"),
    ),
    TaskSpec(
        "cooldown-alarm-filter",
        r"""
namespace cooldown_alarm {
std::vector<std::int64_t> accepted(
    const std::vector<std::int64_t>& requested, std::int64_t cooldown,
    std::int64_t reset_gap) {
    if (cooldown < 0 || reset_gap < 0) throw std::invalid_argument("threshold");
    std::vector<std::int64_t> out;
    std::optional<std::int64_t> last_request, last_accepted;
    for (const auto time:requested) {
        if (last_request && time < *last_request) throw std::invalid_argument("order");
        if (last_request && time-*last_request >= reset_gap) last_accepted.reset();
        if (!last_accepted || time-*last_accepted >= cooldown) {
            out.push_back(time); last_accepted=time;
        }
        last_request=time;
    }
    return out;
}
}
""",
        r"""
int main() {
    using cooldown_alarm::accepted;
    assert((accepted({0,2,5},5,100)==std::vector<std::int64_t>{0,5}));
    assert((accepted({1,1,2},0,100)==std::vector<std::int64_t>{1,1,2}));
    assert((accepted({0,4,20},25,16)==std::vector<std::int64_t>{0,20}));
    assert((accepted({},2,3).empty()));
    bool bad=false; try { (void)accepted({2,1},1,1); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
    bad=false; try { (void)accepted({},-1,2); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "time-*last_request >= reset_gap",
        "time-*last_request > reset_gap",
        "cooldown-reset-filter",
        ("cooldown", "reset-gap", "stable-filter"),
    ),
    TaskSpec(
        "watermark-reorder-buffer",
        r"""
namespace watermark_clock {
std::vector<Event> release(const std::vector<Event>& arrivals, std::int64_t lateness) {
    if (lateness < 0) throw std::invalid_argument("lateness");
    using Key=std::tuple<std::int64_t,int,std::size_t>;
    std::priority_queue<Key,std::vector<Key>,std::greater<Key>> heap;
    std::vector<Event> out;
    std::int64_t maximum=std::numeric_limits<std::int64_t>::min();
    for (std::size_t i=0;i<arrivals.size();++i) {
        maximum=std::max(maximum,arrivals[i].timestamp);
        heap.emplace(arrivals[i].timestamp,arrivals[i].sequence,i);
        const auto watermark=maximum-lateness;
        while (!heap.empty() && std::get<0>(heap.top())<=watermark) {
            const auto [time,sequence,index]=heap.top(); heap.pop();
            (void)index; out.push_back({time,sequence});
        }
    }
    while (!heap.empty()) {
        const auto [time,sequence,index]=heap.top(); heap.pop();
        (void)index; out.push_back({time,sequence});
    }
    return out;
}
}
""",
        r"""
int main() {
    using watermark_clock::Event; using watermark_clock::release;
    auto a=release({{5,0},{3,0},{4,0}},3);
    assert(a.size()==3 && a[0].timestamp==3 && a[2].timestamp==5);
    auto b=release({{2,2},{2,1}},0);
    assert(b[0].sequence==2 && b[1].sequence==1);
    auto c=release({},4); assert(c.empty());
    auto d=release({{10,0},{1,0}},2); assert(d.size()==2);
    bool bad=false; try { (void)release({},-1); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "while (!heap.empty() && std::get<0>(heap.top())<=watermark)",
        "while (!heap.empty() && std::get<0>(heap.top())<watermark)",
        "watermark-buffer",
        ("watermark", "min-heap", "late-event"),
    ),
    TaskSpec(
        "skew-segment-calibration",
        r"""
namespace skew_clock {
static Segment fit(const std::vector<Pair>& points,std::size_t begin,std::size_t end) {
    const auto n=static_cast<double>(end-begin+1);
    double sx=0,sy=0,sxx=0,sxy=0;
    for (std::size_t i=begin;i<=end;++i) {
        const double x=static_cast<double>(points[i].reference);
        const double y=static_cast<double>(points[i].local);
        sx+=x; sy+=y; sxx+=x*x; sxy+=x*y;
    }
    const double denominator=n*sxx-sx*sx;
    const double slope=std::abs(denominator)<1e-18?0.0:(n*sxy-sx*sy)/denominator;
    return {begin,end,slope,(sy-slope*sx)/n};
}
std::vector<Segment> calibrate(const std::vector<Pair>& points,double limit) {
    if (limit < 0) throw std::invalid_argument("limit");
    for (std::size_t i=1;i<points.size();++i)
        if (points[i-1].reference>=points[i].reference) throw std::invalid_argument("reference");
    std::vector<Segment> out;
    std::size_t begin=0;
    while (begin<points.size()) {
        std::size_t best=begin;
        for (std::size_t end=begin;end<points.size();++end) {
            const auto segment=fit(points,begin,end);
            double residual=0;
            for (std::size_t i=begin;i<=end;++i)
                residual=std::max(residual,std::abs(points[i].local-
                    (segment.slope*points[i].reference+segment.intercept)));
            if (residual<=limit) best=end; else break;
        }
        out.push_back(fit(points,begin,best)); begin=best+1;
    }
    return out;
}
}
""",
        r"""
int main() {
    using skew_clock::Pair; using skew_clock::calibrate;
    auto a=calibrate({{0,1},{1,3},{2,5}},0.0);
    assert(a.size()==1 && std::abs(a[0].slope-2.0)<1e-12);
    auto b=calibrate({{0,0},{1,1},{2,9}},0.1); assert(b.size()==2);
    assert(calibrate({},1).empty());
    auto c=calibrate({{4,7}},0); assert(c.size()==1 && c[0].begin==0);
    bool bad=false; try { (void)calibrate({{1,1},{1,2}},0); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "if (residual<=limit)",
        "if (residual<limit)",
        "piecewise-affine-calibration",
        ("least-squares", "maximal-segment", "residual"),
    ),
    TaskSpec(
        "vector-clock-frontier",
        r"""
namespace vector_frontier {
std::vector<std::size_t> maximal_events(const std::vector<Stamp>& events) {
    if (events.empty()) return {};
    const auto dimensions=events.front().size();
    for (const auto& stamp:events)
        if (stamp.size()!=dimensions) throw std::invalid_argument("dimensions");
    std::vector<std::size_t> out;
    for (std::size_t i=0;i<events.size();++i) {
        bool duplicate=false, dominated=false;
        for (std::size_t j=0;j<events.size();++j) {
            if (i==j) continue;
            if (events[i]==events[j] && j<i) { duplicate=true; break; }
            bool all=true,strict=false;
            for (std::size_t k=0;k<dimensions;++k) {
                all=all && events[i][k]<=events[j][k];
                strict=strict || events[i][k]<events[j][k];
            }
            if (all && strict) { dominated=true; break; }
        }
        if (!duplicate && !dominated) out.push_back(i);
    }
    return out;
}
}
""",
        r"""
int main() {
    using vector_frontier::maximal_events;
    assert((maximal_events({{1,1},{2,2},{3,3}})==std::vector<std::size_t>{2}));
    assert((maximal_events({{2,0},{0,2}})==std::vector<std::size_t>{0,1}));
    assert((maximal_events({{1,1},{1,1}})==std::vector<std::size_t>{0}));
    assert(maximal_events({}).empty());
    bool bad=false; try { (void)maximal_events({{1},{1,2}}); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "strict=strict || events[i][k]<events[j][k];",
        "strict=strict || events[i][k]<=events[j][k];",
        "vector-antichain",
        ("partial-order", "causal-frontier", "antichain"),
    ),
    TaskSpec(
        "angular-hand-encounters",
        r"""
namespace hand_encounters {
std::vector<double> times(double ha,double ma,double hr,double mr,double horizon) {
    if (!std::isfinite(ha+ma+hr+mr+horizon) || horizon<0)
        throw std::invalid_argument("input");
    constexpr double turn=360.0;
    const double phase=ha-ma, rate=hr-mr, eps=1e-10;
    if (std::abs(rate)<eps) {
        const double normalized=std::remainder(phase,turn);
        return std::abs(normalized)<eps?std::vector<double>{0.0}:std::vector<double>{};
    }
    const double low=std::min(phase/turn,(phase+rate*horizon)/turn);
    const double high=std::max(phase/turn,(phase+rate*horizon)/turn);
    const auto first=static_cast<long long>(std::ceil(low-eps));
    const auto last=static_cast<long long>(std::floor(high+eps));
    std::vector<double> out;
    for (auto k=first;k<=last;++k) {
        const double time=(turn*k-phase)/rate;
        if (time>=-eps && time<=horizon+eps) out.push_back(std::max(0.0,std::min(horizon,time)));
    }
    std::sort(out.begin(),out.end());
    return out;
}
}
""",
        r"""
int main() {
    using hand_encounters::times;
    auto a=times(0,0,1,0,720); assert(a.size()==3);
    assert(std::abs(a.front())<1e-9 && std::abs(a.back()-720)<1e-9);
    assert(times(10,20,1,1,5).empty());
    auto b=times(10,10,1,1,5); assert(b.size()==1 && b[0]==0);
    auto c=times(180,0,-1,0,180); assert(c.size()==1 && std::abs(c[0]-180)<1e-9);
    bool bad=false; try { (void)times(0,0,1,0,-1); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "time<=horizon+eps",
        "time<horizon-eps",
        "angular-congruence",
        ("continuous-angle", "winding", "closed-horizon"),
    ),
    TaskSpec(
        "sla-business-budget",
        r"""
namespace sla_budget {
std::optional<std::int64_t> deadline(
    std::int64_t start,std::int64_t budget,const std::vector<Window>& service) {
    if (budget<0) throw std::invalid_argument("budget");
    std::int64_t previous=std::numeric_limits<std::int64_t>::min();
    for (const auto& window:service) {
        if (window.begin>window.end || window.begin<previous) throw std::invalid_argument("windows");
        previous=window.end;
    }
    if (budget==0) return start;
    auto cursor=start;
    for (const auto& window:service) {
        if (window.end<=cursor) continue;
        cursor=std::max(cursor,window.begin);
        const auto available=window.end-cursor;
        if (budget<=available) return cursor+budget;
        budget-=available; cursor=window.end;
    }
    return std::nullopt;
}
}
""",
        r"""
int main() {
    using sla_budget::Window; using sla_budget::deadline;
    const std::vector<Window> windows{{0,10},{20,30}};
    assert(deadline(0,5,windows)==5);
    assert(deadline(15,5,windows)==25);
    assert(deadline(5,5,windows)==10);
    assert(deadline(0,20,windows)==30);
    assert(!deadline(0,21,windows));
    assert(deadline(17,0,windows)==17);
    bool bad=false; try { (void)deadline(0,1,{{0,5},{4,8}}); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "if (budget<=available)",
        "if (budget<available)",
        "service-window-budget",
        ("business-window", "capacity", "deadline"),
    ),
    TaskSpec(
        "jitter-cluster-centers",
        r"""
namespace jitter_clock {
std::vector<std::int64_t> centers(std::vector<std::int64_t> ticks,std::int64_t tolerance) {
    if (tolerance<0) throw std::invalid_argument("tolerance");
    std::sort(ticks.begin(),ticks.end());
    std::vector<std::int64_t> out;
    for (std::size_t begin=0;begin<ticks.size();) {
        std::size_t end=begin+1;
        while (end<ticks.size() && ticks[end]-ticks[end-1]<=tolerance) ++end;
        out.push_back(ticks[begin+(end-begin-1)/2]);
        begin=end;
    }
    return out;
}
}
""",
        r"""
int main() {
    using jitter_clock::centers;
    assert((centers({1,2,9},1)==std::vector<std::int64_t>{1,9}));
    assert((centers({0,2,4},2)==std::vector<std::int64_t>{2}));
    assert((centers({4,1,3,2},10)==std::vector<std::int64_t>{2}));
    assert(centers({},0).empty());
    assert((centers({5,5},0)==std::vector<std::int64_t>{5}));
    bool bad=false; try { (void)centers({},-1); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "ticks[end]-ticks[end-1]<=tolerance",
        "ticks[end]-ticks[end-1]<tolerance",
        "jitter-single-linkage",
        ("cluster", "lower-median", "tolerance"),
    ),
    TaskSpec(
        "phase-locked-loop-trace",
        r"""
namespace pll_trace {
static std::int64_t checked_add(std::int64_t a,std::int64_t b) {
    if ((b>0 && a>std::numeric_limits<std::int64_t>::max()-b) ||
        (b<0 && a<std::numeric_limits<std::int64_t>::min()-b))
        throw std::overflow_error("add");
    return a+b;
}
static std::int64_t checked_mul(std::int64_t a,std::int64_t b) {
    if (a==0 || b==0) return 0;
    const auto maximum=std::numeric_limits<std::int64_t>::max();
    const auto minimum=std::numeric_limits<std::int64_t>::min();
    if ((a>0 && b>0 && a>maximum/b) ||
        (a>0 && b<0 && b<minimum/a) ||
        (a<0 && b>0 && a<minimum/b) ||
        (a<0 && b<0 && a<maximum/b))
        throw std::overflow_error("mul");
    return a*b;
}
static std::int64_t normalize(std::int64_t value,std::int64_t modulus) {
    const auto r=value%modulus; return r<0?r+modulus:r;
}
std::vector<State> replay(State state,const std::vector<std::int64_t>& errors,
    std::int64_t phase_gain,std::int64_t frequency_gain,std::int64_t modulus) {
    if (modulus<=0) throw std::invalid_argument("modulus");
    state.phase=normalize(state.phase,modulus);
    std::vector<State> out;
    for (const auto error:errors) {
        state.phase=normalize(checked_add(checked_add(state.phase,state.frequency),
                                         checked_mul(phase_gain,error)),modulus);
        state.frequency=checked_add(state.frequency,checked_mul(frequency_gain,error));
        out.push_back(state);
    }
    return out;
}
}
""",
        r"""
int main() {
    using pll_trace::State; using pll_trace::replay;
    auto a=replay({0,2},{1,1},3,1,10);
    assert(a.size()==2 && a[0].phase==5 && a[0].frequency==3);
    assert(a[1].phase==1 && a[1].frequency==4);
    auto b=replay({0,0},{-1},2,0,5); assert(b[0].phase==3);
    auto c=replay({9,7},{4},3,2,1); assert(c[0].phase==0);
    assert(replay({0,0},{},1,1,7).empty());
    bool bad=false; try { (void)replay({0,0},{},1,1,0); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "checked_mul(phase_gain,error)",
        "checked_mul(frequency_gain,error)",
        "integer-pll-replay",
        ("phase-normalization", "ordered-update", "overflow"),
    ),
    TaskSpec(
        "temporal-quorum-window",
        r"""
namespace temporal_quorum {
std::optional<std::pair<std::int64_t,std::int64_t>> shortest_window(
    const std::vector<Vote>& votes,int members,int quorum) {
    if (members<=0 || quorum<=0 || quorum>members) throw std::invalid_argument("quorum");
    auto sorted=votes;
    for (const auto& vote:sorted)
        if (vote.member<0 || vote.member>=members) throw std::invalid_argument("member");
    std::sort(sorted.begin(),sorted.end(),[](const Vote& a,const Vote& b) {
        return std::tie(a.time,a.member)<std::tie(b.time,b.member);
    });
    std::vector<int> counts(static_cast<std::size_t>(members),0);
    int distinct=0; std::size_t left=0;
    std::optional<std::pair<std::int64_t,std::int64_t>> best;
    for (std::size_t right=0;right<sorted.size();++right) {
        if (counts[static_cast<std::size_t>(sorted[right].member)]++==0) ++distinct;
        while (distinct>=quorum) {
            const auto candidate=std::make_pair(sorted[left].time,sorted[right].time);
            if (!best || candidate.second-candidate.first<best->second-best->first ||
                (candidate.second-candidate.first==best->second-best->first && candidate<*best))
                best=candidate;
            if (--counts[static_cast<std::size_t>(sorted[left].member)]==0) --distinct;
            ++left;
        }
    }
    return best;
}
}
""",
        r"""
int main() {
    using temporal_quorum::Vote; using temporal_quorum::shortest_window;
    assert((shortest_window({{0,1},{1,5},{2,8}},3,2)==std::make_pair<std::int64_t,std::int64_t>(5,8)));
    assert((shortest_window({{0,1},{0,2},{1,9}},2,2)==std::make_pair<std::int64_t,std::int64_t>(2,9)));
    assert((shortest_window({{1,7}},3,1)==std::make_pair<std::int64_t,std::int64_t>(7,7)));
    assert(!shortest_window({},2,2));
    auto tie=shortest_window({{0,0},{1,3},{0,6},{1,9}},2,2); assert(tie && tie->first==0);
    bool bad=false; try { (void)shortest_window({},2,3); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "while (distinct>=quorum)",
        "while (distinct>quorum)",
        "distinct-member-window",
        ("quorum", "sliding-window", "tie-break"),
    ),
)

BY_SLUG = {spec.slug: spec for spec in SPECS}
if len(BY_SLUG) != 15:
    raise ValueError("Clock owner must define exactly 15 unique tasks")
