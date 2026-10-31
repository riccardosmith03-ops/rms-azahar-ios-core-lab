#!/bin/bash
set -euo pipefail
carrier="$(cd "$(dirname "$0")/.." && pwd)"
source_dir="$(cd "$1" && pwd)"
build_dir="$2"
test ! -e "$build_dir"
python3 "$carrier/scripts/verify-source.py" --upstream "$source_dir" --phase before
git -c core.autocrlf=false -C "$source_dir" apply --check "$carrier/patches/0001-rms-runtime-layout.patch"
git -c core.autocrlf=false -C "$source_dir" apply "$carrier/patches/0001-rms-runtime-layout.patch"
python3 "$carrier/scripts/verify-source.py" --upstream "$source_dir" --phase after
# Host-only state-policy test: no iOS binary is executed on the runner.
xcrun --sdk macosx clang++ -std=c++17 -I"$source_dir/src" \
  "$carrier/tests/runtime_layout_policy_test.cpp" -o "$RUNNER_TEMP/rms-layout-policy-test"
"$RUNNER_TEMP/rms-layout-policy-test"
# Based on the fixed upstream libretro-ios recipe; iOS JIT remains disabled.
cmake -S "$source_dir" -B "$build_dir" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DENABLE_LIBRETRO=ON -DIOS=ON \
  -DCMAKE_SYSTEM_NAME=iOS -DCMAKE_SYSTEM_PROCESSOR=arm64 \
  -DCMAKE_OSX_SYSROOT=iphoneos -DCMAKE_OSX_ARCHITECTURES=arm64 \
  -DCMAKE_OSX_DEPLOYMENT_TARGET=17.4 \
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
  -DCMAKE_C_FLAGS=-DIOS -DCMAKE_CXX_FLAGS=-DIOS \
  -DCITRA_USE_PRECOMPILED_HEADERS=OFF -DENABLE_LTO=OFF \
  -DENABLE_TESTS=OFF -DBUILD_TESTING=OFF \
  -DENABLE_BUILTIN_KEYBLOB=OFF
cmake --build "$build_dir" --target citra_libretro --config Release --parallel 2
python3 "$carrier/scripts/verify-source.py" --upstream "$source_dir" --phase after
test -f "$build_dir/bin/Release/azahar_libretro.dylib"
printf '%s\n' 'Core compilation completed; packaging inspection is still required.'
