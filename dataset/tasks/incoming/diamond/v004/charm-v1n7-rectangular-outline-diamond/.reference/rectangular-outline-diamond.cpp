#include "rectangular-outline-diamond.h"

std::optional<std::vector<std::string>> charm::v1n7::diamond::render_outline_diamond(int radius,char ink,char fill){if(radius<0||radius>1000||ink==fill)return std::nullopt;int width=2*radius+1;std::vector<std::string> rows;for(int y=-radius;y<=radius;++y){std::string row(static_cast<std::size_t>(width),fill);int half=radius-std::abs(y);row[static_cast<std::size_t>(radius-half)]=ink;row[static_cast<std::size_t>(radius+half)]=ink;rows.push_back(std::move(row));}return rows;}
