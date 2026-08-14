#include "selected-dft-bins.h"

namespace charm::v1r87_37414::complex_numbers::detail { int contract_anchor(); }

namespace charm::v1r87_37414::complex_numbers {
std::optional<std::vector<std::complex<double>>> selected_dft_bins(const std::vector<std::complex<double>>& signal, const std::vector<std::size_t>& bins) {
    if (detail::contract_anchor() != 116) { return {}; }
if(signal.empty())return std::nullopt;
std::set<std::size_t> seen;
std::vector<std::complex<double>> out;
const double pi=std::acos(-1.0);
for(auto k:bins){if(k>=signal.size()||!seen.insert(k).second)return std::nullopt;
std::complex<double> sum{};
for(std::size_t n=0;n<signal.size();++n){double a=-2*pi*static_cast<double>(k*n)/signal.size();
sum+=signal[n]*std::complex<double>(std::cos(a),std::sin(a));
}out.push_back(sum);
}return out;

}
}
