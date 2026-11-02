RMS / AZAHAR â€” PORTABLE iPHONEOS CORE BUILD CANDIDATE

STATUS: local preparation only. Not compiled, uploaded, dispatched or installed.
The runtime layout patch and the build recipe still need a real Mac build and device tests.
No IPA or standalone app is produced. This is one unsigned libretro framework for RetroArch.

Fixed official source: https://github.com/azahar-emu/azahar
Commit f570b53f9c9bcf42b0741afdd8cf0a6dfa5f98f5, tag 2127.0-alpha3.
Source submodules are the revisions recorded by that commit, not latest branches.
source-lock.json guards the patch, its original/patched files and critical CMake sources.
The patch is GPL-compatible source only. The upstream license is LICENSE.txt.

Manual workflow only: macos-26 standard runner, 120-minute maximum, two compiler jobs.
It checks out the fixed source, verifies hashes/submodules, applies the guarded patch,
runs a host-only state-policy test, and builds target citra_libretro for native iPhoneOS
arm64 with minimum iOS 17.4. Apple provides its SDK on the runner; no SDK is distributed.
No personal file, ROM, firmware, key, credential, signing identity or paid service is included.
The builtin keyblob option is explicitly OFF. Normal user-provided decrypted content remains
outside this project. Compilation/runtime success is not claimed.

The recipe is based on the fixed upstream .github/workflows/libretro.yml iOS job,
src/citra_libretro/CMakeLists.txt and the root/externals CMake sources. It preserves IOS
compiler definitions, Vulkan and FastInterp defaults. It disables PCH, LTO and tests to bound
build resources. BUILD_TESTING=OFF is the real Oaknut guard. The stale upstream ENABLE_OPT
flag is omitted because the current Crypto++ CMake defines different flags; no guessed
optimization or JIT flag is added. CPU JIT now has an experimental default-off iOS option; shader JIT remains disabled.
The guest CPU clock, audio and libretro timing are unchanged. No dependency host dylib is allowed in the packaged core.

Runtime option citra_rms_layout_hotkey defaults to disabled, preserving original controls.
Available modes: r3, r2, l3 and l3_r2. The user wants the SAME physical button that changes
views in DS. DS cycles on logical R3, so r3 is the first candidate after checking actual MFi
mapping; no assertion is made that a physically labelled RT is always logical R2.
All enabled layout modes bypass the old L3 screen-swap action; disabled restores it.
R3 mode consumes the controller stylus-click role, while physical touchscreen/mouse input
remain available. R2 mode consumes ZR instead. L3 replaces Home/swap. L3+R2 preserves R2 alone
as ZR, including when L3 is released before R2. The selected shortcut changes only two views:
side_by_side (Both) and single_screen with TOP. Edge-triggered, no repeat while held, requires
release after loading with a held button, resets between games. No options/save files are
written by the hotkey. Hiding BOTTOM releases an emulated stylus already held down.

Packaging requires thin arm64 MH_DYLIB, native iOS platform, minimum 17.4, all 25 libretro ABI
exports and only Apple system dynamic dependencies. It corrects the install name on a copy,
removes any link-time signature, strips local symbols and emits azahar.libretro.framework /
azahar.libretro with an unsigned framework plist and SHA/CRC inspection record. The framework
name matches the existing core naming convention. Runtime installation/signing/trust and
backup/rollback are a separate, later device operation. No installation script is included.
The artifact includes this portable source recipe, patch, lock and GPL license. For complete
corresponding upstream/dependency sources use the fixed public commit and its submodules;
no release publication is performed by this workflow.

30 FPS GAMEPLAY PERFORMANCE REMAINS UNMEASURED. The optional Vulkan30 output mode below changes
frontend cadence while retaining two complete60Hz guest frames per call. Guest CPU clock,
audio generation and PICA rendering remain unchanged. Neither stable full-speed gameplay
nor reduced CPU/GPU cost is promised. The separate40FPS request remains unimplemented.

Required later checks: actual compiler result; static package inspection; retain current
framework/configs; sign/trust under the existing jailbreak flow; test physical mapping,
Both/Top transitions and held-button behavior; touch after returning from TOP; rotation;
controller disconnect/reconnect; ordinary in-game save/close/reopen; normal audio/game clock.
Keep quickstates disabled and preserve all complete per-game options, especially Ultrasole1x
and Rubino2x. No forced restart during a game with unsaved progress.

EXPERIMENTAL CPU JIT CANDIDATE â€” LOCAL, NOT BUILT OR DEVICE TESTED
Option citra_ios_cpu_jit defaults to disabled. jit_if_available runs a bounded
RX -> RW -> emit -> icache -> RX worker test inside the actual RetroArch process,
verifying return42 and then return43 after rewriting the same allocation. A failed
probe chooses FastInterp before the exclusive monitor or any CPU core is created.
Changing the option while content is running is deferred until close/reopen.

This is an opt-in experiment, not a 30 FPS cap or a measured speed improvement.
The code does not enable kernel/debug permissions or use MAP_JIT. CS_DEBUGGED or
a JIT flag alone is not treated as capability proof. A kernel signing failure
while invoking the probe may still terminate the app; it cannot be caught as an
ordinary syscall failure. No signal handler is installed to hide that outcome.

Oaknut iOS mmap/MAP_FAILED and RW/RX protection results are checked on every use.
After JIT selection, a code-memory allocation/protection failure prints only a
fixed phase and errno, then terminates RetroArch with _Exit(86). This includes
initial Dynarmic construction after a successful probe. It is NOT a graceful
content stop: the app exits, unsaved gameplay may be lost, no C++ exception is
unwound through generated frames, and no live interpreter fallback is attempted.
Keep ordinary in-game saves and leave this option disabled during normal use.

Host mock policy tests cover failed allocation, first/second RW and RX failure,
wrong emitted return value, cleanup and the successful two-call ordering. They
use no executable memory. The unchanged RT/R3 policy tests remain included.
A future authorized Mac build and explicit on-device testing are still required.


EXPERIMENTAL VULKAN30 OUTPUT CANDIDATE — NOT BUILT OR DEVICE TESTED
Option citra_rms_output_fps defaults to60. Select30 per game, then close/reopen
content. Selection is frozen during retro_load_game, before initial AV-info
query; context_reset is later. Live option changes are deferred to content reload.
30 mode refuses soft reset, quick states and context replacement; close/reopen
content instead. It retains all published slots through a refused soft reset.
Normal in-game saves are
unaffected. Non-Vulkan content retains60. A compliant libretro frontend
queries AV info only after successful content load; RetroArch1.22.2 follows this.

At30 the frontend calls retro_run30times/sec and each call completes two entire
guest frames. Both VBlanks, guest CPU/PICA work, input polls and audio generation
remain. Both internal set_image AND video_cb calls are omitted while both
boundaries still complete. The second image is staged, then published exactly
once after both Core RunLoops return and the final GPU work has been drained.
This is not frontend slow motion, a guest CPU underclock or a PICA/draw discard.

Each raw frontend sync index owns a distinct image, view, framebuffer and
persistent descriptor. The frame vector remains fixed for that renderer. Only
the slot released by wait_sync_index may be changed or resized; all other
images and metadata stay alive, including across RT layout changes. No modulo
mapping aliases different frontend indices. Mask changes and secondary output
windows are refused. Queue idle alone is not used as a frontend image lease.

The Vulkan interface/device/queue identity and required callbacks are validated.
An immutable interface snapshot is captured before the Scheduler exists; Begin
and context reset never write a worker-shared interface while the renderer lives.
One frontend wait_sync_index/get_sync_index is cached across both guest frames.
Initially, between guest frames and after BOTH RunLoops, the core drains Finish
and WaitWorker, then takes submit_mutex followed by the frontend queue lock and
waits for graphics queue idle. These conservative waits can REDUCE throughput;
they make no performance promise. Missing/changed interfaces or synchronization
failures latch the run stopped and request frontend shutdown, with no silent
one-frame/two-frame fallback under mismatched frontend timing.

The existing host policy test now covers load-latching, deferred changes, hidden
internal images, one late publication, reset/reentry/failure behavior, raw index
leases/mask holes/slot31 and the30calls/two-frames clock arithmetic. It does not
run a GPU, audio or real game.
Mac compilation, static artifact checks and separately authorized device tests
remain required. Validate normal game clock/audio plus actual output images;
a30FPS counter alone is insufficient evidence of full-speed gameplay.
