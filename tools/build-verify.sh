#!/usr/bin/env bash
# Requires an already provisioned ESP-IDF toolchain. Does not flash.
set -euo pipefail
profile="${C5_BOARD_PROFILE:-waveshare}"
case "$profile" in
    waveshare)
        build_dir=build
        config_file=sdkconfig
        defaults_file=sdkconfig.defaults
        ;;
    cyd)
        build_dir=build-cyd
        config_file="$PWD/build-cyd/sdkconfig"
        defaults_file="$PWD/boards/nm-cyd-c5/sdkconfig.defaults"
        ;;
    *) echo "Unsupported C5_BOARD_PROFILE: $profile" >&2; exit 2 ;;
esac
mkdir -p "$build_dir/evidence"
{
    git rev-parse HEAD
    git status --porcelain --untracked-files=no
    idf.py --version
    git -C "$IDF_PATH" rev-parse HEAD
    git -C "$IDF_PATH" describe --always --dirty
    riscv32-esp-elf-gcc --version
    python --version
    cmake --version
    ninja --version
    echo "Profile: $profile"
    echo "Defaults: $defaults_file"
} > "$build_dir/evidence/toolchain.txt"
if [ "$profile" = cyd ]; then
    idf.py -B "$build_dir" -DSDKCONFIG="$config_file" \
        -DSDKCONFIG_DEFAULTS="$defaults_file" build 2>&1 | tee "$build_dir/evidence/build.log"
else
    idf.py -B "$build_dir" build 2>&1 | tee "$build_dir/evidence/build.log"
fi
python -m esptool --chip esp32c5 image-info "$build_dir/c5_uart_tool.bin" > "$build_dir/evidence/app-image.txt"
python -m esptool --chip esp32c5 image-info "$build_dir/bootloader/bootloader.bin" > "$build_dir/evidence/bootloader-image.txt"
python "$IDF_PATH/components/partition_table/gen_esp32part.py" "$build_dir/partition_table/partition-table.bin" > "$build_dir/evidence/partitions.csv"
C5_BOARD_PROFILE="$profile" C5_SDKCONFIG_FILE="$config_file" C5_DEFAULTS_FILE="$defaults_file" \
    python tools/verify_artifacts.py "$build_dir"
