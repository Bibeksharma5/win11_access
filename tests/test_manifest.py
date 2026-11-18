# -*- coding: UTF-8 -*-
import os
import unittest
import re

class TestManifest(unittest.TestCase):
    def setUp(self):
        self.manifest_path = os.path.join(os.path.dirname(__file__), "..", "addon", "manifest.ini")

    def test_manifest_exists(self):
        self.assertTrue(os.path.isfile(self.manifest_path), "manifest.ini must exist")

    def test_manifest_keys(self):
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            content = f.read()

        def get_val(key):
            m = re.search(rf'^{key}\s*=\s*(.+)$', content, re.MULTILINE)
            if not m:
                return None
            val = m.group(1).strip()
            if val.startswith('"""'):
                # multiline
                m2 = re.search(rf'^{key}\s*=\s*"""(.*?)"""', content, re.DOTALL | re.MULTILINE)
                return m2.group(1).strip() if m2 else val
            return val.strip('"\'')

        self.assertEqual(get_val("name"), "win11_access")
        self.assertEqual(get_val("summary"), "Accessibility enhancement for windows 11")
        self.assertEqual(get_val("version"), "1.1")
        self.assertEqual(get_val("author"), "Bibek Sharma Dhakal")
        self.assertEqual(get_val("minimumNVDAVersion"), "2026.1")
        self.assertEqual(get_val("lastTestedNVDAVersion"), "2026.3")

if __name__ == "__main__":
    unittest.main()
