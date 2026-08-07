#include <cctype>
#include <cmath>
#include <string>
#include <string_view>
#include <vector>
namespace charm::cryptosquare {
class StreamingEncoder {
public:
    bool append(std::string_view chunk) {
        if (done_) return false;
        for (unsigned char ch : chunk) if (std::isalnum(ch)) text_.push_back(static_cast<char>(std::tolower(ch)));
        return true;
    }
    std::string finish() {
        if (done_) return result_;
        done_ = true;
        if (text_.empty()) return result_;
        const std::size_t columns = static_cast<std::size_t>(std::ceil(std::sqrt(static_cast<long double>(text_.size()))));
        const std::size_t rows = (text_.size() + columns - 1) / columns;
        for (std::size_t column = 0; column < columns; ++column) {
            if (column != 0) result_.push_back(' ');
            for (std::size_t row = 0; row < rows; ++row) {
                const std::size_t index = row * columns + column;
                if (index < text_.size()) result_.push_back(text_[index]);
            }
        }
        return result_;
    }
    bool finished() const { return done_; }
private:
    std::string text_;
    std::string result_;
    bool done_ = false;
};
}
