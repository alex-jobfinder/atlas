import unittest

from atlas_dearpygui_gui.utils.default_dataset_loader import (
    load_default_dataset,
    format_dataset,
)


class TestDefaultDatasetLoader(unittest.TestCase):
    def test_load_and_format(self):
        raw = load_default_dataset()
        self.assertIn("plots", raw)

        formatted = format_dataset(raw)
        self.assertIn("time_series", formatted)
        self.assertGreater(len(formatted["time_series"]), 0)

        first = formatted["time_series"][0]
        self.assertIsInstance(first["data"]["startTime"], (int, float))
        self.assertIn("metadata", formatted)
        self.assertEqual(formatted["metadata"]["source"], "default_dataset")


if __name__ == "__main__":
    unittest.main()
