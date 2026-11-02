// Standalone policy tests for the later authorized C++ build; not yet compiled/run.
#include <cassert>
#include <vector>
#include "core/arm/ios_jit_policy.h"
#include "citra_libretro/runtime_layout_hotkey.h"
using LibRetro::RuntimeLayoutHotkey;
using LibRetro::RuntimeLayoutState;
namespace {
struct MockCodeMemory {
    std::vector<int> trace;
    int fail_writable = 0, fail_executable = 0;
    int writable_calls = 0, executable_calls = 0, invocations = 0, releases = 0;
    bool fail_allocate = false, wrong_value = false, fail_release = false;
    std::uint32_t instruction = 0;
    int LastError() const { return 13; }
    bool Allocate() { trace.push_back(1); return !fail_allocate; }
    bool MakeWritable() { trace.push_back(2); return ++writable_calls != fail_writable; }
    void Emit(std::uint32_t value) { trace.push_back(3); instruction = value; }
    void Invalidate() { trace.push_back(4); }
    bool MakeExecutable() { trace.push_back(5); return ++executable_calls != fail_executable; }
    std::uint64_t Execute() { trace.push_back(6); ++invocations; return wrong_value ? 0 : (instruction == 0xD2800540U ? 42 : 43); }
    bool Release() { trace.push_back(7); ++releases; return !fail_release; }
};
void TestIOSCodeMemoryPolicy() {
    using namespace Core::IOSJit;
    MockCodeMemory pass;
    assert(ProbeMemory(pass).Passed());
    assert((pass.trace == std::vector<int>{1,2,3,4,5,6,2,3,4,5,6,7}));
    assert(pass.invocations == 2 && pass.releases == 1);
    MockCodeMemory allocation; allocation.fail_allocate = true;
    assert(ProbeMemory(allocation).phase == ProbePhase::Allocate);
    assert((allocation.trace == std::vector<int>{1}) && allocation.releases == 0);
    MockCodeMemory rw; rw.fail_writable = 1;
    assert(ProbeMemory(rw).phase == ProbePhase::Writable);
    assert((rw.trace == std::vector<int>{1,2,7}) && rw.invocations == 0);
    MockCodeMemory rx; rx.fail_executable = 1;
    assert(ProbeMemory(rx).phase == ProbePhase::Executable);
    assert((rx.trace == std::vector<int>{1,2,3,4,5,7}) && rx.invocations == 0);
    MockCodeMemory second_rw; second_rw.fail_writable = 2;
    assert(ProbeMemory(second_rw).phase == ProbePhase::Writable && second_rw.invocations == 1 && second_rw.releases == 1);
    MockCodeMemory second_rx; second_rx.fail_executable = 2;
    assert(ProbeMemory(second_rx).phase == ProbePhase::Executable && second_rx.invocations == 1 && second_rx.releases == 1);
    MockCodeMemory value; value.wrong_value = true;
    assert(ProbeMemory(value).phase == ProbePhase::Value && value.invocations == 1 && value.releases == 1);
    MockCodeMemory release; release.fail_release = true;
    assert(ProbeMemory(release).phase == ProbePhase::Release && release.releases == 1);
}
} // namespace

int main() {
    TestIOSCodeMemoryPolicy();
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
