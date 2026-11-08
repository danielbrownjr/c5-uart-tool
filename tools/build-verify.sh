#!/usr/bin/env bash
# Run only inside an already provisioned ESP-IDF environment. Never flashes.
set -euo pipefail
mkdir -p build/evidence
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
} > build/evidence/toolchain.txt
idf.py build 2>&1 | tee build/evidence/build.log
python -m esptool --chip esp32c5 image-info build/c5_uart_tool.bin > build/evidence/app-image.txt
python -m esptool --chip esp32c5 image-info build/bootloader/bootloader.bin > build/evidence/bootloader-image.txt
python "$IDF_PATH/components/partition_table/gen_esp32part.py" build/partition_table/partition-table.bin > build/evidence/partitions.csv
python tools/verify_artifacts.py build
