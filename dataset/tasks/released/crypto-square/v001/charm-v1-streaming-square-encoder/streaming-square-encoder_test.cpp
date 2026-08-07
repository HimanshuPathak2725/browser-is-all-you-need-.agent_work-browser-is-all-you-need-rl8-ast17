#include "streaming-square-encoder.cpp"
#include <cassert>
#include <string>
using charm::cryptosquare::StreamingEncoder;
int main() {
    StreamingEncoder encoder;
    assert(!encoder.finished());
    assert(encoder.append("Ab!"));
    assert(encoder.append(" c12"));
    const std::string first = encoder.finish();
    assert(first == "a1 b2 c ");
    assert(encoder.finished() && encoder.finish() == first);
    assert(!encoder.append("ignored") && encoder.finish() == first);
    StreamingEncoder empty;
    assert(empty.finish().empty() && empty.finished());
    StreamingEncoder chunks;
    assert(chunks.append("a") && chunks.append("b") && chunks.finish() == "a b");
    return 0;
}
