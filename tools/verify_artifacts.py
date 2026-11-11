#!/usr/bin/env python3
"""Check the chosen board profile and retain linked, hashed build artifacts."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def verify_configs(config, generated, expected):
    """Validate IDF's generated configuration as well as sdkconfig text."""
    for key, value in expected.items():
        text_value = config.get('CONFIG_' + key)
        require(text_value == value, f'Unexpected effective {key}: {text_value}')
        generated_value = generated.get(key)
        # Kconfig booleans are 'y' in sdkconfig but true in SDKCONFIG JSON.
        expected_json = True if value == 'y' else value
        require(generated_value == expected_json,
                f'Generated configuration mismatch for {key}: {generated_value!r} != {expected_json!r}')
    require(config.get('CONFIG_SPIRAM') != 'y', 'PSRAM is not part of this profile')
    require(generated.get('SPIRAM') not in (True, 'y'),
            'Generated configuration unexpectedly enables PSRAM')
    other = 'C5_BOARD_WAVESHARE' if 'C5_BOARD_CYD' in expected else 'C5_BOARD_CYD'
    require(config.get('CONFIG_' + other) != 'y' and generated.get(other) not in (True, 'y'),
            'Competing board profile enabled')


def main(build):
    build = Path(build)
    profile = os.environ.get('C5_BOARD_PROFILE', 'waveshare')
    require(profile in ('waveshare', 'cyd'), f'Unsupported profile: {profile}')
    size = '16MB' if profile == 'cyd' else '32MB'
    size_header = 0x4F if profile == 'cyd' else 0x5F
    flag = 'C5_BOARD_CYD' if profile == 'cyd' else 'C5_BOARD_WAVESHARE'
    config_path = Path(os.environ.get('C5_SDKCONFIG_FILE', 'sdkconfig'))
    defaults_path = Path(os.environ.get('C5_DEFAULTS_FILE', 'sdkconfig.defaults'))
    config = {}
    for line in config_path.read_text().splitlines():
        if line.startswith('CONFIG_') and '=' in line:
            key, value = line.split('=', 1)
            config[key] = value.strip('"')
    expected = {'IDF_TARGET': 'esp32c5', 'ESPTOOLPY_FLASHSIZE': size,
                'ESPTOOLPY_FLASHSIZE_' + size: 'y', flag: 'y', 'ESPTOOLPY_FLASHMODE': 'dio',
                'ESPTOOLPY_FLASHFREQ': '80m', 'PARTITION_TABLE_SINGLE_APP': 'y',
                'ESP_CONSOLE_NONE': 'y', 'ESP_CONSOLE_SECONDARY_NONE': 'y',
                'C5_UART_RX_GPIO': '4', 'C5_UART_BAUD': '115200'}
    generated = json.loads((build / 'config/sdkconfig.json').read_text())
    verify_configs(config, generated, expected)
    args = json.loads((build / 'flasher_args.json').read_text())
    require(args['flash_settings']['flash_size'] == size, 'Flash arguments disagree')
    require(args['flash_settings']['flash_mode'] == 'dio', 'Unexpected flash mode')
    require(args['flash_settings']['flash_freq'] == '80m', 'Unexpected flash frequency')
    images = args['flash_files']
    # Preserve ESP-IDF single-app default placement; no capacity-driven expansion.
    require(set(int(offset, 0) for offset in images) == {0x2000, 0x8000, 0x10000},
            f'Unexpected flash layout: {images}')
    for name in ('c5_uart_tool.bin', 'bootloader/bootloader.bin'):
        image = (build / name).read_bytes()
        require(image[0] == 0xE9 and image[2] == 2 and image[3] == size_header
                and int.from_bytes(image[12:14], 'little') == 23,
                f'{name}: expected ESP32-C5 image, DIO, 80 MHz, {size} header')
    entries = []
    partition_bytes = (build / 'partition_table/partition-table.bin').read_bytes()
    for offset in range(0, len(partition_bytes), 32):
        magic, kind, subtype, address, size, label, flags = struct.unpack_from('<HBBII16sI', partition_bytes, offset)
        if magic != 0x50AA:
            break  # MD5 record or erased padding; IDF decoder validates the digest.
        entries.append((label.rstrip(b'\0').decode(), kind, subtype, address, size, flags))
    require(entries == [('nvs', 1, 2, 0x9000, 0x6000, 0),
                        ('phy_init', 1, 1, 0xF000, 0x1000, 0),
                        ('factory', 0, 0, 0x10000, 0x100000, 0)],
            f'Unexpected partition entries: {entries}')
    table = (build / 'evidence/partitions.csv').read_text()
    require('factory' in table and '0x10000' in table and '1M' in table,
            'Unexpected single-app partition table')
    destination = build / 'retained'
    destination.mkdir(exist_ok=True)
    required = [*images.values(), 'c5_uart_tool.elf', 'c5_uart_tool.map',
                'flasher_args.json', 'flash_args', 'project_description.json',
                'config/sdkconfig.json', 'compile_commands.json']
    for name in required:
        source = build / name
        require(source.is_file(), f'Missing artifact {source}')
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    shutil.copyfile(config_path, destination / 'sdkconfig')
    shutil.copyfile(defaults_path, destination / 'sdkconfig.defaults')
    shutil.copytree(build / 'evidence', destination / 'evidence', dirs_exist_ok=True)
    def git(*args):
        return subprocess.check_output(['git', *args], text=True).strip()
    require(not git('diff', '--stat', 'HEAD'), 'Tracked source modified during build')
    manifest = {'source_sha': git('rev-parse', 'HEAD'), 'target': 'esp32c5',
                'board_profile': ('RockBase NM-CYD-C5 16 MB (not device-measured)' if profile == 'cyd'
                                  else 'Waveshare NXRX 32R8U (capacity not device-measured)'),
                'idf_sha': git('-C', os.environ['IDF_PATH'], 'rev-parse', 'HEAD'),
                'ci_run': os.environ.get('GITHUB_RUN_ID'), 'effective_profile': expected,
                'physical_validation': False, 'files': {}}
    for path in sorted(destination.rglob('*')):
        if path.is_file() and path.name != 'manifest.json':
            manifest['files'][str(path.relative_to(destination))] = {
                'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'build')
