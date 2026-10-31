// Standalone policy tests for the later authorized C++ build; not yet compiled/run.
#include <cassert>
#include "citra_libretro/runtime_layout_hotkey.h"
using LibRetro::RuntimeLayoutHotkey;
using LibRetro::RuntimeLayoutState;
int main() {
    using K = RuntimeLayoutHotkey;
    RuntimeLayoutState s;
    assert(!s.Update(K::Disabled, true, true, false, false));
    // A trigger held while loading must not change the initial view.
    assert(s.Update(K::R2, false, true, false, false));
    assert(!s.TopOnly());
    s.Update(K::R2, false, true, false, false); assert(!s.TopOnly());
    s.Update(K::R2, false, false, false, false); assert(!s.TopOnly());
    s.Update(K::R2, false, true, false, false); assert(s.TopOnly());
    // Held RT never oscillates. An unrelated option refresh cannot reset the view.
    for (int i = 0; i < 120; ++i) {
        s.Update(K::R2, false, true, false, false); assert(s.TopOnly());
    }
    s.Update(K::R2, false, false, false, false);
    s.Update(K::R2, false, true, false, false); assert(!s.TopOnly());
    // Mode changes arm only after release, and start from the current configured view.
    s.Update(K::L3, true, false, false, true); assert(s.TopOnly());
    s.Update(K::L3, false, false, false, true);
    s.Update(K::L3, true, false, false, true); assert(!s.TopOnly());
    assert(!s.Update(K::Disabled, false, false, false, false));
    s.Update(K::L3R2, false, false, false, false);
    s.Update(K::L3R2, false, true, false, false); assert(!s.TopOnly());
    s.Update(K::L3R2, true, true, false, false); assert(s.TopOnly());
    s.Update(K::L3R2, true, true, false, false); assert(s.TopOnly());
    // Direct RT owns ZR. Combo mode preserves RT alone; disabled owns nothing.
    assert(LibRetro::RuntimeLayoutConsumesR2(K::R2, false));
    assert(!LibRetro::RuntimeLayoutConsumesR2(K::L3R2, false));
    assert(LibRetro::RuntimeLayoutConsumesR2(K::L3R2, true));
    assert(!LibRetro::RuntimeLayoutConsumesR2(K::Disabled, true));
    assert(!LibRetro::RuntimeLayoutConsumesL3(K::R2));
    assert(LibRetro::RuntimeLayoutConsumesL3(K::L3));
    assert(LibRetro::RuntimeLayoutConsumesL3(K::L3R2));
    assert(!LibRetro::RuntimeLayoutConsumesL3(K::Disabled));
    s.Reset(); s.Update(K::R3, false, false, false, false);
    s.Update(K::R3, false, false, true, false); assert(s.TopOnly());
    s.Update(K::R3, false, false, true, false); assert(s.TopOnly());
    s.Update(K::R3, false, false, false, false);
    s.Update(K::R3, false, false, true, false); assert(!s.TopOnly());
    // A new game starts in its own configured view, without a leaked prior latch.
    s.Reset(); s.Update(K::R2, false, false, false, true); assert(s.TopOnly());
    s.Update(K::R2, false, true, false, true); assert(!s.TopOnly());
}
