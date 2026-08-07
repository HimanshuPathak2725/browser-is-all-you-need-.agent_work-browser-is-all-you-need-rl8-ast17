"""Complex-number task definitions for the four-topic 60-task batch."""

from __future__ import annotations

from .common import TaskSpec


SPECS = (
    TaskSpec(
        "stable-quadratic-pair",
        r"""
namespace stable_quadratic {
std::pair<std::complex<double>,std::complex<double>> roots(double a,double b,double c) {
    if (!std::isfinite(a+b+c) || a==0.0) throw std::invalid_argument("quadratic");
    const std::complex<double> discriminant(b*b-4.0*a*c,0.0);
    const auto radical=std::sqrt(discriminant);
    const auto signed_radical=b>=0.0?radical:-radical;
    const auto q=-0.5*(std::complex<double>(b,0.0)+signed_radical);
    std::complex<double> first,second;
    if (std::abs(q)==0.0) first=second=-b/(2.0*a);
    else { first=q/a; second=c/q; }
    const auto key=[](const auto& z){return std::make_pair(z.real(),z.imag());};
    if (key(second)<key(first)) std::swap(first,second);
    return {first,second};
}
}
""",
        r"""
int main() {
    using stable_quadratic::roots;
    auto a=roots(1,-3,2); assert(std::abs(a.first.real()-1)<1e-12 && std::abs(a.second.real()-2)<1e-12);
    auto b=roots(1,2,1); assert(std::abs(b.first.real()+1)<1e-12 && std::abs(b.second.real()+1)<1e-12);
    auto c=roots(1,0,1); assert(std::abs(std::abs(c.first)-1)<1e-12 && c.first.imag()<0);
    auto d=roots(1,1e16,1); assert(std::abs(d.first*d.second-std::complex<double>(1,0))<1e-6);
    bool bad=false; try { (void)roots(0,1,2); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "const auto q=-0.5*",
        "const auto q=0.5*",
        "stable-quadratic",
        ("cancellation-resistant", "complex-root", "vieta"),
    ),
    TaskSpec(
        "hermitian-symmetry-audit",
        r"""
namespace hermitian_audit {
std::vector<Mismatch> audit(
    const std::vector<std::complex<double>>& spectrum,double tolerance) {
    if (tolerance<0 || !std::isfinite(tolerance)) throw std::invalid_argument("tolerance");
    std::vector<Mismatch> out;
    const auto n=spectrum.size();
    for (std::size_t left=0;left<n;++left) {
        const auto right=(n-left)%n;
        if (left>right) continue;
        const double error=left==right?std::abs(spectrum[left].imag())
            :std::abs(spectrum[left]-std::conj(spectrum[right]));
        const double scale=1.0+std::max(std::abs(spectrum[left]),std::abs(spectrum[right]));
        if (error>tolerance*scale) out.push_back({left,right,error});
    }
    return out;
}
}
""",
        r"""
int main() {
    using hermitian_audit::audit;
    assert(audit({},0).empty());
    assert(audit({{1,0},{2,3},{4,0},{2,-3}},1e-12).empty());
    auto a=audit({{1,2}},0); assert(a.size()==1 && a[0].left==0);
    auto b=audit({{1,0},{2,1},{2,1}},0); assert(b.size()==1);
    assert(audit({{1,0},{2,3},{4,0},{2,-3}},1).empty());
    bool bad=false; try { (void)audit({},-1); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "if (error>tolerance*scale)",
        "if (error>=tolerance*scale)",
        "hermitian-audit",
        ("conjugate-symmetry", "self-bin", "scaled-tolerance"),
    ),
    TaskSpec(
        "gaussian-integer-gcd",
        r"""
namespace gaussian_gcd {
static Gaussian multiply(Gaussian a,Gaussian b) {
    return {a.real*b.real-a.imag*b.imag,a.real*b.imag+a.imag*b.real};
}
static Gaussian subtract(Gaussian a,Gaussian b) { return {a.real-b.real,a.imag-b.imag}; }
static std::int64_t nearest(long double value) {
    const auto lower=std::floor(value), fraction=value-lower;
    return static_cast<std::int64_t>(fraction>0.5L?lower+1:lower);
}
static Gaussian remainder(Gaussian a,Gaussian b) {
    const long double norm=static_cast<long double>(b.real)*b.real+
                           static_cast<long double>(b.imag)*b.imag;
    const auto qr=nearest((static_cast<long double>(a.real)*b.real+
                           static_cast<long double>(a.imag)*b.imag)/norm);
    const auto qi=nearest((static_cast<long double>(a.imag)*b.real-
                           static_cast<long double>(a.real)*b.imag)/norm);
    return subtract(a,multiply({qr,qi},b));
}
static bool zero(Gaussian value) { return value.real==0 && value.imag==0; }
Gaussian gcd(Gaussian a,Gaussian b) {
    if (zero(a) && zero(b)) return {0,0};
    while (!zero(b)) { const auto r=remainder(a,b); a=b; b=r; }
    std::array<Gaussian,4> associates{a,{-a.imag,a.real},{-a.real,-a.imag},{a.imag,-a.real}};
    auto best=associates[0];
    bool found=false;
    for (const auto candidate:associates) {
        if (candidate.real>0 && candidate.imag>=0 &&
            (!found || std::tie(candidate.real,candidate.imag)<std::tie(best.real,best.imag))) {
            best=candidate; found=true;
        }
    }
    if (!found) {
        for (const auto candidate:associates)
            if (candidate.real==0 && candidate.imag>0) return candidate;
    }
    return best;
}
}
""",
        r"""
int main() {
    using gaussian_gcd::Gaussian; using gaussian_gcd::gcd;
    auto z=gcd({0,0},{0,0}); assert(z.real==0 && z.imag==0);
    auto a=gcd({2,0},{0,0}); assert(a.real==2 && a.imag==0);
    auto b=gcd({5,0},{2,1}); assert(b.real==2 && b.imag==1);
    auto c=gcd({-2,0},{0,0}); assert(c.real==2 && c.imag==0);
    auto d=gcd({1,1},{1,-1}); assert(d.real==1 && d.imag==1);
}
""",
        "candidate.real>0 && candidate.imag>=0",
        "candidate.real<0 && candidate.imag>=0",
        "gaussian-euclid",
        ("gaussian-integer", "nearest-lattice", "unit-normalization"),
    ),
    TaskSpec(
        "branch-continuous-log",
        r"""
namespace branch_log {
std::vector<std::complex<double>> continuous_log(
    const std::vector<std::complex<double>>& path) {
    constexpr double pi=3.141592653589793238462643383279502884;
    std::vector<std::complex<double>> out;
    std::optional<double> previous;
    for (const auto value:path) {
        const auto magnitude=std::abs(value);
        if (!(magnitude>0) || !std::isfinite(magnitude)) throw std::invalid_argument("path");
        double angle=std::arg(value);
        if (previous) {
            const auto turns=std::floor((*previous-angle)/(2*pi)+0.5);
            angle+=turns*2*pi;
            if (std::abs(angle-*previous-pi)<1e-12) angle-=2*pi;
        }
        out.emplace_back(std::log(magnitude),angle); previous=angle;
    }
    return out;
}
}
""",
        r"""
int main() {
    using branch_log::continuous_log;
    assert(continuous_log({}).empty());
    auto a=continuous_log({{1,0},{-1,0},{0,-1}});
    assert(a.size()==3 && std::abs(a[0].imag())<1e-12);
    assert(std::abs(a[1].imag()+3.141592653589793)<1e-12);
    assert(std::abs(a[2].imag()+1.5707963267948966)<1e-12);
    auto b=continuous_log({{2,0}}); assert(std::abs(b[0].real()-std::log(2.0))<1e-12);
    bool bad=false; try { (void)continuous_log({{0,0}}); } catch(const std::invalid_argument&) { bad=true; }
    auto crossing=continuous_log({std::polar(1.0,3.0),std::polar(1.0,-3.0)}); assert(crossing[1].imag()>3.0);
    assert(bad);
}
""",
        "angle+=turns*2*pi;",
        "angle-=turns*2*pi;",
        "continuous-complex-log",
        ("branch-cut", "phase-unwrapping", "nonzero-path"),
    ),
    TaskSpec(
        "complex-two-by-two-solve",
        r"""
namespace complex_linear2 {
std::optional<Solution> solve(
    std::array<std::complex<double>,4> a,
    std::array<std::complex<double>,2> b,double epsilon) {
    if (epsilon<0) throw std::invalid_argument("epsilon");
    const auto determinant=a[0]*a[3]-a[1]*a[2];
    const double scale=std::max({std::abs(a[0]),std::abs(a[1]),std::abs(a[2]),std::abs(a[3]),1.0});
    if (std::abs(determinant)<=epsilon*scale*scale) return std::nullopt;
    const auto x=(b[0]*a[3]-a[1]*b[1])/determinant;
    const auto y=(a[0]*b[1]-b[0]*a[2])/determinant;
    const auto r0=a[0]*x+a[1]*y-b[0], r1=a[2]*x+a[3]*y-b[1];
    return Solution{x,y,std::max(std::abs(r0),std::abs(r1))};
}
}
""",
        r"""
int main() {
    using complex_linear2::solve; using C=std::complex<double>;
    auto a=solve({C(1,0),C(0,0),C(0,0),C(1,0)},{C(2,1),C(3,-1)},1e-12);
    assert(a && std::abs(a->x-C(2,1))<1e-12 && a->residual<1e-12);
    auto b=solve({C(0,0),C(1,0),C(1,0),C(0,0)},{C(2,0),C(3,0)},1e-12);
    assert(b && std::abs(b->x-C(3,0))<1e-12);
    assert(!solve({C(1,0),C(1,0),C(2,0),C(2,0)},{C(1,0),C(2,0)},1e-12));
    bool bad=false; try { (void)solve({},{},-1); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "std::abs(determinant)<=epsilon*scale*scale",
        "std::abs(determinant)<epsilon",
        "complex-linear-solve",
        ("scaled-singularity", "residual-certificate", "two-by-two"),
    ),
    TaskSpec(
        "barycentric-complex-interpolation",
        r"""
namespace complex_barycentric {
std::complex<double> interpolate(
    const std::vector<std::complex<double>>& nodes,
    const std::vector<std::complex<double>>& values,std::complex<double> query) {
    if (nodes.empty() || nodes.size()!=values.size()) throw std::invalid_argument("sizes");
    std::vector<std::complex<double>> weights(nodes.size(),1.0);
    for (std::size_t i=0;i<nodes.size();++i) {
        if (query==nodes[i]) return values[i];
        for (std::size_t j=0;j<nodes.size();++j) if (i!=j) {
            if (nodes[i]==nodes[j]) throw std::invalid_argument("duplicate");
            weights[i]/=nodes[i]-nodes[j];
        }
    }
    std::complex<double> numerator=0,denominator=0;
    for (std::size_t i=0;i<nodes.size();++i) {
        const auto term=weights[i]/(query-nodes[i]);
        numerator+=term*values[i]; denominator+=term;
    }
    return numerator/denominator;
}
}
""",
        r"""
int main() {
    using complex_barycentric::interpolate; using C=std::complex<double>;
    assert(std::abs(interpolate({C(0,0)},{C(4,2)},C(7,1))-C(4,2))<1e-12);
    assert(std::abs(interpolate({C(0,0),C(1,0)},{C(1,0),C(3,0)},C(.5,0))-C(2,0))<1e-12);
    assert(interpolate({C(0,0),C(1,0)},{C(1,0),C(3,0)},C(1,0))==C(3,0));
    bool bad=false; try { (void)interpolate({}, {}, C(0,0)); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
    bad=false; try { (void)interpolate({C(1,0),C(1,0)},{C(2,0),C(3,0)},C(0,0)); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "return numerator/denominator;",
        "return denominator/numerator;",
        "complex-barycentric",
        ("interpolation", "barycentric-weight", "exact-node"),
    ),
    TaskSpec(
        "phase-unwrapping-dp",
        r"""
namespace phase_dp {
std::vector<double> unwrap(
    const std::vector<double>& wrapped,double penalty,int max_step) {
    if (penalty<0 || max_step<0) throw std::invalid_argument("penalty");
    if (wrapped.empty()) return {};
    constexpr double turn=6.283185307179586476925286766559;
    const int bound=max_step*static_cast<int>(wrapped.size());
    const double infinity=std::numeric_limits<double>::infinity();
    std::vector<double> previous(static_cast<std::size_t>(2*bound+1),infinity),current;
    std::vector<std::vector<int>> parent(wrapped.size(),std::vector<int>(static_cast<std::size_t>(2*bound+1),0));
    previous[static_cast<std::size_t>(bound)]=0;
    for (std::size_t i=1;i<wrapped.size();++i) {
        current.assign(previous.size(),infinity);
        for (int k=-bound;k<=bound;++k) for (int pk=-bound;pk<=bound;++pk) {
            if (std::abs(k-pk)>max_step || !std::isfinite(previous[static_cast<std::size_t>(pk+bound)])) continue;
            const double delta=(wrapped[i]+turn*k)-(wrapped[i-1]+turn*pk);
            const double cost=previous[static_cast<std::size_t>(pk+bound)]+delta*delta+
                              penalty*static_cast<double>((k-pk)*(k-pk));
            auto& best=current[static_cast<std::size_t>(k+bound)];
            if (cost<best-1e-12 || (std::abs(cost-best)<1e-12 && pk<parent[i][static_cast<std::size_t>(k+bound)])) {
                best=cost; parent[i][static_cast<std::size_t>(k+bound)]=pk;
            }
        }
        previous.swap(current);
    }
    int winding=-bound;
    for (int k=-bound;k<=bound;++k)
        if (previous[static_cast<std::size_t>(k+bound)]<
            previous[static_cast<std::size_t>(winding+bound)]-1e-12) winding=k;
    std::vector<double> out(wrapped.size());
    for (std::size_t i=wrapped.size();i-- >0;) {
        out[i]=wrapped[i]+turn*winding;
        if (i>0) winding=parent[i][static_cast<std::size_t>(winding+bound)];
    }
    return out;
}
}
""",
        r"""
int main() {
    using phase_dp::unwrap;
    auto d=unwrap({0,3.5},10,1); assert(std::abs(d[1]-3.5)<1e-12);
    assert(unwrap({},1,1).empty());
    auto a=unwrap({3.0,-3.0},0,1); assert(a.size()==2 && std::abs(a[1]-a[0])<1);
    auto b=unwrap({0,0,0},2,1); assert(std::abs(b[2])<1e-12);
    auto c=unwrap({1,2},0,0); assert(c[0]==1 && c[1]==2);
    bool bad=false; try { (void)unwrap({1},-1,1); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "penalty*static_cast<double>((k-pk)*(k-pk))",
        "0.0*static_cast<double>((k-pk)*(k-pk))",
        "phase-dynamic-program",
        ("winding-dp", "jump-penalty", "tie-reconstruction"),
    ),
    TaskSpec(
        "complex-reflection-chain",
        r"""
namespace reflection_chain {
std::complex<double> apply(
    std::complex<double> value,const std::vector<Mirror>& mirrors) {
    for (const auto& mirror:mirrors) {
        const auto length=std::abs(mirror.direction);
        if (!(length>0)) throw std::invalid_argument("direction");
        const auto unit=mirror.direction/length;
        const auto local=(value-mirror.point)/unit;
        value=mirror.point+unit*std::conj(local);
    }
    return value;
}
}
""",
        r"""
int main() {
    using reflection_chain::Mirror; using reflection_chain::apply; using C=std::complex<double>;
    assert(std::abs(apply(C(2,3),{{C(0,0),C(1,0)}})-C(2,-3))<1e-12);
    assert(std::abs(apply(C(2,3),{{C(0,0),C(0,1)}})-C(-2,3))<1e-12);
    assert(std::abs(apply(C(1,0),{{C(0,0),C(1,0)}})-C(1,0))<1e-12);
    auto a=apply(C(1,2),{{C(0,0),C(1,0)},{C(0,0),C(0,1)}});
    auto b=apply(C(1,2),{{C(0,0),C(0,1)},{C(0,0),C(1,0)}});
    assert(std::abs(a-b)<1e-12);
    bool bad=false; try { (void)apply(C(0,0),{{C(0,0),C(0,0)}}); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "unit*std::conj(local)",
        "unit*local",
        "oriented-line-reflection",
        ("reflection", "complex-frame", "ordered-transform"),
    ),
    TaskSpec(
        "newton-basin-label",
        r"""
namespace newton_basin {
Result classify(const std::vector<std::complex<double>>& coefficients,
    std::complex<double> value,int maximum,double tolerance) {
    if (coefficients.size()<2 || maximum<0 || tolerance<0)
        throw std::invalid_argument("newton");
    for (int iteration=0;iteration<=maximum;++iteration) {
        std::complex<double> polynomial=coefficients[0],derivative=0;
        for (std::size_t i=1;i<coefficients.size();++i) {
            derivative=derivative*value+polynomial;
            polynomial=polynomial*value+coefficients[i];
        }
        if (std::abs(polynomial)<=tolerance) return {0,iteration,value};
        if (iteration==maximum || std::abs(derivative)<=tolerance) return {-1,iteration,value};
        value-=polynomial/derivative;
    }
    return {-1,maximum,value};
}
}
""",
        r"""
int main() {
    using newton_basin::classify; using C=std::complex<double>;
    auto a=classify({C(1,0),C(0,0),C(-1,0)},C(2,0),20,1e-10);
    assert(a.root_index==0 && std::abs(a.final_value-C(1,0))<1e-6);
    auto b=classify({C(1,0),C(0,0),C(-1,0)},C(0,0),20,1e-10);
    assert(b.root_index==-1);
    auto c=classify({C(1,0),C(-1,0)},C(1,0),0,0); assert(c.root_index==0);
    bool bad=false; try { (void)classify({C(1,0)},C(0,0),1,1); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "if (std::abs(polynomial)<=tolerance)",
        "if (std::abs(polynomial)<tolerance)",
        "complex-newton",
        ("horner-derivative", "convergence-label", "iteration-limit"),
    ),
    TaskSpec(
        "complex-covariance-eigenpair",
        r"""
namespace covariance2 {
Eigenpair principal(const std::vector<std::array<std::complex<double>,2>>& samples) {
    if (samples.size()<2) throw std::invalid_argument("samples");
    std::array<std::complex<double>,2> mean{0.0,0.0};
    for (const auto& sample:samples) { mean[0]+=sample[0]; mean[1]+=sample[1]; }
    mean[0]/=static_cast<double>(samples.size()); mean[1]/=static_cast<double>(samples.size());
    double a=0,d=0; std::complex<double> b=0;
    for (const auto& sample:samples) {
        const auto x=sample[0]-mean[0], y=sample[1]-mean[1];
        a+=std::norm(x); d+=std::norm(y); b+=x*std::conj(y);
    }
    const double divisor=static_cast<double>(samples.size()-1);
    a/=divisor; d/=divisor; b/=divisor;
    const double value=(a+d+std::sqrt((a-d)*(a-d)+4*std::norm(b)))/2;
    std::array<std::complex<double>,2> vector;
    if (std::abs(b)>1e-15) vector={b,std::complex<double>(value-a,0)};
    else vector=a>=d?std::array<std::complex<double>,2>{1.0,0.0}
                    :std::array<std::complex<double>,2>{0.0,1.0};
    const double length=std::sqrt(std::norm(vector[0])+std::norm(vector[1]));
    vector[0]/=length; vector[1]/=length;
    const auto pivot=std::abs(vector[0])>1e-15?vector[0]:vector[1];
    const auto phase=std::conj(pivot)/std::abs(pivot);
    vector[0]*=phase; vector[1]*=phase;
    return {value,vector};
}
}
""",
        r"""
int main() {
    using covariance2::principal; using C=std::complex<double>;
    auto a=principal({{{C(0,0),C(0,0)}},{{C(2,0),C(0,0)}}});
    assert(std::abs(a.value-2.0)<1e-12 && std::abs(a.vector[0].real()-1)<1e-12);
    auto b=principal({{{C(0,0),C(0,0)}},{{C(0,0),C(2,0)}}});
    assert(std::abs(b.vector[1].real()-1)<1e-12);
    auto c=principal({{{C(1,1),C(2,0)}},{{C(2,1),C(3,0)}},{{C(3,1),C(4,0)}}});
    assert(c.value>=0 && c.vector[0].real()>=-1e-12);
    bool bad=false; try { (void)principal({{{C(0,0),C(0,0)}}}); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "a>=d?",
        "a<d?",
        "hermitian-covariance",
        ("covariance", "principal-eigenpair", "canonical-phase"),
    ),
    TaskSpec(
        "integer-complex-power",
        r"""
namespace integer_power {
std::complex<double> powi(std::complex<double> base,std::int64_t exponent) {
    if (exponent<0 && base==std::complex<double>(0,0)) throw std::domain_error("zero");
    const bool negative=exponent<0;
    std::uint64_t magnitude=negative
        ?static_cast<std::uint64_t>(-(exponent+1))+1
        :static_cast<std::uint64_t>(exponent);
    std::complex<double> result=1.0;
    while (magnitude) {
        if (magnitude&1U) result*=base;
        magnitude>>=1U;
        if (magnitude) base*=base;
    }
    return negative?1.0/result:result;
}
}
""",
        r"""
int main() {
    using integer_power::powi; using C=std::complex<double>;
    assert(powi(C(2,0),0)==C(1,0));
    assert(powi(C(0,1),2)==C(-1,0));
    assert(std::abs(powi(C(2,0),-3)-C(.125,0))<1e-12);
    auto a=powi(C(1,0),std::numeric_limits<std::int64_t>::min()); assert(a==C(1,0));
    assert(powi(C(0,0),3)==C(0,0));
    bool bad=false; try { (void)powi(C(0,0),-1); } catch(const std::domain_error&) { bad=true; }
    assert(bad);
}
""",
        "return negative?1.0/result:result;",
        "return result;",
        "signed-binary-power",
        ("exponentiation-by-squaring", "int64-min", "reciprocal"),
    ),
    TaskSpec(
        "complex-polygon-winding",
        r"""
namespace complex_winding {
int winding_number(const std::vector<std::complex<double>>& polygon,
    std::complex<double> query) {
    if (polygon.size()<3) throw std::invalid_argument("polygon");
    int winding=0;
    const auto cross=[&](auto a,auto b) {
        return (b.real()-a.real())*(query.imag()-a.imag())-
               (query.real()-a.real())*(b.imag()-a.imag());
    };
    for (std::size_t i=0;i<polygon.size();++i) {
        const auto a=polygon[i], b=polygon[(i+1)%polygon.size()];
        const double area=cross(a,b);
        const double dot=(query.real()-a.real())*(query.real()-b.real())+
                         (query.imag()-a.imag())*(query.imag()-b.imag());
        if (std::abs(area)<1e-12 && dot<=0) throw std::domain_error("boundary");
        if (a.imag()<=query.imag() && b.imag()>query.imag() && area>0) ++winding;
        if (a.imag()>query.imag() && b.imag()<=query.imag() && area<0) --winding;
    }
    return winding;
}
}
""",
        r"""
int main() {
    using complex_winding::winding_number; using C=std::complex<double>;
    std::vector<C> square{{0,0},{2,0},{2,2},{0,2}};
    assert(winding_number(square,C(1,1))==1);
    std::reverse(square.begin(),square.end()); assert(winding_number(square,C(1,1))==-1);
    assert(winding_number(square,C(3,3))==0);
    std::vector<C> bow{{0,0},{2,2},{0,2},{2,0}}; assert(winding_number(bow,C(3,1))==0);
    bool bad=false; try { (void)winding_number(square,C(0,0)); } catch(const std::domain_error&) { bad=true; }
    assert(bad);
}
""",
        "area>0) ++winding",
        "area<0) ++winding",
        "polygon-winding",
        ("ray-crossing", "signed-winding", "boundary-rejection"),
    ),
    TaskSpec(
        "biquad-frequency-extrema",
        r"""
namespace biquad_extrema {
std::pair<double,double> sampled_extrema(Coefficients c,std::size_t samples) {
    if (samples<2) throw std::invalid_argument("samples");
    constexpr double pi=3.141592653589793238462643383279502884;
    double minimum=std::numeric_limits<double>::infinity(),maximum=0;
    for (std::size_t i=0;i<samples;++i) {
        const double omega=pi*static_cast<double>(i)/static_cast<double>(samples-1);
        const auto z=std::polar(1.0,-omega),z2=z*z;
        const auto numerator=c.b0+c.b1*z+c.b2*z2;
        const auto denominator=1.0+c.a1*z+c.a2*z2;
        if (std::abs(denominator)<=1e-14) throw std::domain_error("pole");
        const double magnitude=std::abs(numerator/denominator);
        minimum=std::min(minimum,magnitude); maximum=std::max(maximum,magnitude);
    }
    return {minimum,maximum};
}
}
""",
        r"""
int main() {
    using biquad_extrema::Coefficients; using biquad_extrema::sampled_extrema;
    auto a=sampled_extrema({1,0,0,0,0},8); assert(std::abs(a.first-1)<1e-12 && std::abs(a.second-1)<1e-12);
    auto b=sampled_extrema({1,1,0,0,0},3); assert(b.first<1e-12 && std::abs(b.second-2)<1e-12);
    bool bad=false; try { (void)sampled_extrema({1,0,0,0,0},1); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
    bad=false; try { (void)sampled_extrema({1,0,0,-1,0},2); } catch(const std::domain_error&) { bad=true; }
    assert(bad);
}
""",
        "i<samples;++i",
        "i+1<samples;++i",
        "biquad-sampling",
        ("frequency-response", "nyquist", "pole-rejection"),
    ),
    TaskSpec(
        "root-of-unity-permutation",
        r"""
namespace unity_permutation {
static std::size_t bit_count(std::size_t value) {
    std::size_t count=0;
    while(value) { value&=value-1; ++count; }
    return count;
}
std::vector<std::size_t> nearest_bins(
    const std::vector<std::complex<double>>& values,std::size_t order) {
    if (values.size()>order || order==0 || order>20) throw std::invalid_argument("order");
    for (const auto value:values) if (value==std::complex<double>(0,0)) throw std::invalid_argument("zero");
    constexpr double pi=3.141592653589793238462643383279502884;
    const std::size_t states=std::size_t{1}<<order;
    const double inf=std::numeric_limits<double>::infinity();
    std::vector<double> dp(states,inf); std::vector<std::vector<std::size_t>> path(states);
    dp[0]=0;
    for (std::size_t mask=0;mask<states;++mask) {
        const auto index=bit_count(mask);
        if (index>=values.size() || !std::isfinite(dp[mask])) continue;
        for (std::size_t bin=0;bin<order;++bin) if (!(mask&(std::size_t{1}<<bin))) {
            const auto root=std::polar(1.0,2*pi*static_cast<double>(bin)/static_cast<double>(order));
            const auto next=mask|(std::size_t{1}<<bin);
            const auto cost=dp[mask]+std::norm(values[index]-root);
            auto candidate=path[mask]; candidate.push_back(bin);
            if (cost<dp[next]-1e-12 || (std::abs(cost-dp[next])<1e-12 &&
                                       (path[next].empty() || candidate<path[next]))) {
                dp[next]=cost; path[next]=std::move(candidate);
            }
        }
    }
    std::vector<std::size_t> best; double cost=inf;
    for (std::size_t mask=0;mask<states;++mask)
        if (bit_count(mask)==values.size() &&
            (dp[mask]<cost-1e-12 || (std::abs(dp[mask]-cost)<1e-12 &&
                                     (best.empty() || path[mask]<best)))) {
            cost=dp[mask]; best=path[mask];
        }
    return best;
}
}
""",
        r"""
int main() {
    using unity_permutation::nearest_bins; using C=std::complex<double>;
    assert((nearest_bins({C(1,0)},4)==std::vector<std::size_t>{0}));
    assert((nearest_bins({C(1,0),C(-1,0)},4)==std::vector<std::size_t>{0,2}));
    auto a=nearest_bins({C(0,1),C(1,0)},4); assert(a[0]==1 && a[1]==0);
    assert(nearest_bins({},3).empty());
    bool bad=false; try { (void)nearest_bins({C(1,0),C(2,0)},1); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
    bad=false; try { (void)nearest_bins({C(0,0)},2); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "cost<dp[next]-1e-12",
        "cost>dp[next]+1e-12",
        "root-assignment",
        ("roots-of-unity", "bitmask-assignment", "minimum-distance"),
    ),
    TaskSpec(
        "complex-continued-fraction",
        r"""
namespace complex_cf {
static std::int64_t nearest(double value) {
    const double lower=std::floor(value), fraction=value-lower;
    return static_cast<std::int64_t>(fraction>0.5?lower+1:lower);
}
std::vector<Gaussian> expand(std::complex<double> value,std::size_t terms,double epsilon) {
    if (!std::isfinite(value.real()) || !std::isfinite(value.imag()) || epsilon<0)
        throw std::invalid_argument("input");
    std::vector<Gaussian> out;
    for (std::size_t i=0;i<terms;++i) {
        const Gaussian term{nearest(value.real()),nearest(value.imag())};
        out.push_back(term);
        const auto remainder=value-std::complex<double>(term.real,term.imag);
        if (std::abs(remainder)<=epsilon) break;
        value=1.0/remainder;
        if (!std::isfinite(value.real()) || !std::isfinite(value.imag()))
            throw std::overflow_error("remainder");
    }
    return out;
}
}
""",
        r"""
int main() {
    using complex_cf::expand;
    assert(expand({2,3},10,1e-12).size()==1);
    auto a=expand({1.25,0},4,1e-12); assert(a.size()==2 && a[0].real==1 && a[1].real==4);
    assert(expand({1.5,0},1,0)[0].real==1);
    assert(expand({1,1},0,0).empty());
    bool bad=false; try { (void)expand({std::numeric_limits<double>::infinity(),0},1,0); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "fraction>0.5?",
        "fraction>=0.5?",
        "gaussian-continued-fraction",
        ("continued-fraction", "gaussian-rounding", "remainder-inversion"),
    ),
)

BY_SLUG = {spec.slug: spec for spec in SPECS}
if len(BY_SLUG) != 15:
    raise ValueError("Complex Numbers owner must define exactly 15 unique tasks")
