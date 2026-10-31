RMS / AZAHAR — PORTABLE iPHONEOS CORE BUILD CANDIDATE

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
optimization or JIT flag is added. CPU/shader JIT remain hard-disabled by the upstream IOS
parser. No dependency host dylib is allowed in the packaged core.

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

40 FPS REQUEST REMAINS OPEN. This patch does not change video timing, emulation speed, guest
CPU clock, audio, render rate or retro_run pacing. 1x resolution is not a 40 FPS cap. A safe
render-only cap needs separate Vulkan image/fence and duplicate-frame work plus real gameplay
measurement. Neither stable 40 FPS nor improved CPU/GPU cost is promised by this build.

Required later checks: actual compiler result; static package inspection; retain current
framework/configs; sign/trust under the existing jailbreak flow; test physical mapping,
Both/Top transitions and held-button behavior; touch after returning from TOP; rotation;
controller disconnect/reconnect; ordinary in-game save/close/reopen; normal audio/game clock.
Keep quickstates disabled and preserve all complete per-game options, especially Ultrasole1x
and Rubino2x. No forced restart during a game with unsaved progress.
