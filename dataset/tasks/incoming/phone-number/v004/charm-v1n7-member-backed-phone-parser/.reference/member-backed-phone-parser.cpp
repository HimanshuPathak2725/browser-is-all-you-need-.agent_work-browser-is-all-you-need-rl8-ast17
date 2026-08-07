#include "member-backed-phone-parser.h"

std::optional<charm::v1n7::phone_number::NormalizedPhone> charm::v1n7::phone_number::parse_normalized_phone(std::string_view text){std::string main,ext;bool in_extension=false;for(char raw:text){unsigned char c=static_cast<unsigned char>(raw);if(raw=='x'||raw=='X'){if(in_extension)return std::nullopt;in_extension=true;continue;}if(std::isdigit(c)){(in_extension?ext:main).push_back(raw);}else if(std::isalpha(c))return std::nullopt;}if(in_extension&&ext.empty())return std::nullopt;if(main.size()==11&&main.front()=='1')main.erase(main.begin());if(main.size()!=10||main[0]<'2'||main[3]<'2')return std::nullopt;return NormalizedPhone(main,ext);}
charm::v1n7::phone_number::NormalizedPhone::NormalizedPhone(std::string national_digits,std::string extension_digits):digits_(std::move(national_digits)),extension_(std::move(extension_digits)){}
const std::string& charm::v1n7::phone_number::NormalizedPhone::digits() const{return digits_;}
const std::string& charm::v1n7::phone_number::NormalizedPhone::extension() const{return extension_;}
