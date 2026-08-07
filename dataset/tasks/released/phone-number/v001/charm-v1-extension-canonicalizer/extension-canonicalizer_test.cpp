#include "extension-canonicalizer.h"
#include <cassert>
using charm::phone::canonicalize;
int main() {
    const auto plain = canonicalize("(212) 555-0123");
    assert(plain && plain->number == "2125550123" && plain->extension.empty());
    const auto country = canonicalize("+1 212 555 0123 x45");
    assert(country && country->number == "2125550123" && country->extension == "45");
    const auto ext = canonicalize("415.555.9999 ext. 007");
    assert(ext && ext->extension == "007");
    assert(!canonicalize("1125550123"));
    assert(!canonicalize("2121550123"));
    assert(!canonicalize("212CALLNOW"));
    assert(!canonicalize("2125550123 x"));
    assert(!canonicalize("2125550123 x1234567"));
    return 0;
}
