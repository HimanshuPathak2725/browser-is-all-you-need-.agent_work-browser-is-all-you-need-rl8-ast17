#include "encapsulated-complex-value.h"

namespace charm::v1n7::complex_numbers::detail { int contract_anchor(); }

charm::v1n7::complex_numbers::EncapsulatedComplex charm::v1n7::complex_numbers::make_encapsulated_complex(double real,double imag){return EncapsulatedComplex(real,imag);}
charm::v1n7::complex_numbers::EncapsulatedComplex::EncapsulatedComplex(double real,double imag):real_(real),imag_(imag){}
double charm::v1n7::complex_numbers::EncapsulatedComplex::real() const{return real_;}
double charm::v1n7::complex_numbers::EncapsulatedComplex::imag() const{return imag_;}
double charm::v1n7::complex_numbers::EncapsulatedComplex::magnitude_squared() const{return real_*real_+imag_*imag_;}
charm::v1n7::complex_numbers::EncapsulatedComplex charm::v1n7::complex_numbers::EncapsulatedComplex::conjugate() const{return EncapsulatedComplex(real_,-imag_);}
bool charm::v1n7::complex_numbers::EncapsulatedComplex::operator==(const EncapsulatedComplex& other) const{return real_==other.real_&&imag_==other.imag_;}
