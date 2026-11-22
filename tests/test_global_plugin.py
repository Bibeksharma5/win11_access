# -*- coding: UTF-8 -*-
import os
import sys
import unittest

tests_dir = os.path.dirname(__file__)
addon_dir = os.path.join(tests_dir, "..", "addon")
sys.path.insert(0, addon_dir)
sys.path.insert(0, tests_dir)

import nvda_mocks
nvda_mocks.install_mocks()

from globalPlugins.win11_access import GlobalPlugin
from types import SimpleNamespace


class TestGlobalPlugin(unittest.TestCase):
    def test_global_plugin_lifecycle(self):
        plugin = GlobalPlugin()
        # Verify executable registration
        self.assertEqual(
            nvda_mocks.appModuleHandler._registeredExecutables.get("calculatorapp"),
            "calculator"
        )
        self.assertEqual(
            nvda_mocks.appModuleHandler._registeredExecutables.get("calc"),
            "calculator"
        )

        plugin.terminate()
        self.assertNotIn("calculatorapp", nvda_mocks.appModuleHandler._registeredExecutables)
        self.assertNotIn("calc", nvda_mocks.appModuleHandler._registeredExecutables)

    def test_global_plugin_does_not_override_app_level_events(self):
        # GlobalPlugin should no longer have event_gainFocus, event_foreground, or chooseNVDAObjectOverlayClasses
        # because those belong to the respective app modules.
        plugin = GlobalPlugin()
        self.assertFalse(hasattr(plugin, "chooseNVDAObjectOverlayClasses"))
        self.assertFalse(hasattr(plugin, "event_gainFocus"))
        self.assertFalse(hasattr(plugin, "event_foreground"))
        plugin.terminate()

    def test_global_plugin_event_focusEntered(self):
        plugin = GlobalPlugin()
        called = []
        def nextHandler():
            called.append(True)

        obj = SimpleNamespace(
            appModule=SimpleNamespace(appName="notepad"),
            role=nvda_mocks.controlTypes.Role.LIST,
            name="context menu"
        )
        plugin.event_focusEntered(obj, nextHandler)
        self.assertEqual(len(called), 1)
        plugin.terminate()

    def test_focusEntered_propagates_downstream_error_without_retrying(self):
        plugin = GlobalPlugin()
        self.addCleanup(plugin.terminate)
        obj = SimpleNamespace(appModule=SimpleNamespace(appName="unigram"))
        error = RuntimeError("downstream focus handler failed")
        calls = []

        def nextHandler():
            calls.append(True)
            raise error

        with self.assertRaises(RuntimeError) as raised:
            plugin.event_focusEntered(obj, nextHandler)

        self.assertIs(raised.exception, error)
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
