"""Regression checks for generated ESP-IDF configuration consistency."""
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "tools" / "verify_artifacts.py"
SPEC = importlib.util.spec_from_file_location("verify_artifacts", SOURCE)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class GeneratedConfigTests(unittest.TestCase):
    def setUp(self):
        self.expected = {
            "IDF_TARGET": "esp32c5", "ESPTOOLPY_FLASHSIZE": "16MB",
            "ESPTOOLPY_FLASHSIZE_16MB": "y", "C5_BOARD_CYD": "y",
            "C5_UART_BAUD": "115200", "C5_UART_RX_GPIO": "4",
        }
        self.config = {"CONFIG_" + k: v for k, v in self.expected.items()}
        self.generated = {
            k: (True if v == "y" else v) for k, v in self.expected.items()
        }
        # ESP-IDF JSON holds Kconfig numeric options as integers.
        self.generated["C5_UART_BAUD"] = 115200
        self.generated["C5_UART_RX_GPIO"] = 4

    def test_matching_generated_configuration(self):
        module.verify_configs(self.config, self.generated, self.expected)

    def test_stale_generated_baud_is_rejected(self):
        self.generated["C5_UART_BAUD"] = 9600
        with self.assertRaises(SystemExit):
            module.verify_configs(self.config, self.generated, self.expected)

    def test_stale_generated_flash_profile_is_rejected(self):
        self.generated["ESPTOOLPY_FLASHSIZE"] = "32MB"
        with self.assertRaises(SystemExit):
            module.verify_configs(self.config, self.generated, self.expected)

    def test_generated_psram_enablement_is_rejected(self):
        self.generated["SPIRAM"] = True
        with self.assertRaises(SystemExit):
            module.verify_configs(self.config, self.generated, self.expected)

    def test_competing_board_profile_is_rejected(self):
        self.generated["C5_BOARD_WAVESHARE"] = True
        with self.assertRaises(SystemExit):
            module.verify_configs(self.config, self.generated, self.expected)


if __name__ == "__main__":
    unittest.main()
