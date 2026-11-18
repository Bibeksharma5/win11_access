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

from appModules import calculator
from appModules import calculatorapp
from types import SimpleNamespace


class TestCalculator(unittest.TestCase):
    def setUp(self):
        nvda_mocks.ui.messages.clear()
        calculator._announcedCalculatorHwnds.clear()
        nvda_mocks.api._foreground = None
        nvda_mocks.api._focus = None
        nvda_mocks.winUser._window_texts.clear()

    def test_isCalculatorApp(self):
        # Native calculator process
        obj1 = SimpleNamespace(appModule=SimpleNamespace(appName="calculator"))
        self.assertTrue(calculator.isCalculatorApp(obj1))

        obj2 = SimpleNamespace(appModule=SimpleNamespace(appName="CalculatorApp"))
        self.assertTrue(calculator.isCalculatorApp(obj2))

        obj3 = SimpleNamespace(appModule=SimpleNamespace(appName="calc"))
        self.assertTrue(calculator.isCalculatorApp(obj3))

        # ApplicationFrameHost with Calculator window title
        obj_afh = SimpleNamespace(
            appModule=SimpleNamespace(appName="applicationframehost"),
            name="Calculator",
            windowHandle=4001
        )
        nvda_mocks.winUser._window_texts[4001] = "Calculator"
        self.assertTrue(calculator.isCalculatorApp(obj_afh))

        # ApplicationFrameHost for Settings (not Calculator)
        obj_other_afh = SimpleNamespace(
            appModule=SimpleNamespace(appName="applicationframehost"),
            name="Settings",
            windowHandle=4002
        )
        nvda_mocks.winUser._window_texts[4002] = "Settings"
        self.assertFalse(calculator.isCalculatorApp(obj_other_afh))

        # Other app
        obj_np = SimpleNamespace(appModule=SimpleNamespace(appName="notepad"))
        self.assertFalse(calculator.isCalculatorApp(obj_np))

    def test_findElementByAutoId(self):
        header = SimpleNamespace(name="Standard", UIAAutomationId="Header", children=[])
        container = SimpleNamespace(name="", UIAAutomationId="NavView", children=[header])
        root = SimpleNamespace(name="Calculator", UIAAutomationId="", children=[container])

        found = calculator._findElementByAutoId(root, "Header")
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "Standard")

        found_lower = calculator._findElementByAutoId(root, "header")
        self.assertIsNotNone(found_lower)
        self.assertEqual(found_lower.name, "Standard")

        self.assertIsNone(calculator._findElementByAutoId(root, "NonExistent"))

    def test_findKnownModeInDescendants(self):
        mode_elem = SimpleNamespace(name="Scientific", UIAAutomationId="", children=[])
        panel = SimpleNamespace(name="", UIAAutomationId="", children=[mode_elem])
        root = SimpleNamespace(name="Calculator", UIAAutomationId="", children=[panel])

        found_mode = calculator._findKnownModeInDescendants(root)
        self.assertEqual(found_mode, "Scientific")

    def test_getCalculatorMode_via_header(self):
        header = SimpleNamespace(name="Programmer", UIAAutomationId="Header", children=[])
        calc_win = SimpleNamespace(
            name="Calculator",
            appModule=SimpleNamespace(appName="calculator"),
            windowHandle=5001,
            children=[header]
        )
        nvda_mocks.api._foreground = calc_win

        mode = calculator.getCalculatorMode()
        self.assertEqual(mode, "Programmer")

    def test_getCalculatorMode_via_window_title(self):
        calc_win = SimpleNamespace(
            name="Scientific - Calculator",
            appModule=SimpleNamespace(appName="calculator"),
            windowHandle=5002,
            children=[]
        )
        nvda_mocks.winUser._window_texts[5002] = "Scientific - Calculator"
        nvda_mocks.api._foreground = calc_win

        mode = calculator.getCalculatorMode()
        self.assertEqual(mode, "Scientific")

    def test_getCalculatorMode_from_focusObject(self):
        header = SimpleNamespace(name="Standard", UIAAutomationId="Header", children=[])
        calc_root = SimpleNamespace(name="Calculator", appModule=SimpleNamespace(appName="calculatorapp"), children=[header])
        btn = SimpleNamespace(name="Clear", appModule=SimpleNamespace(appName="calculatorapp"), parent=calc_root, children=[])

        nvda_mocks.api._foreground = None
        nvda_mocks.api._focus = btn

        mode = calculator.getCalculatorMode()
        self.assertEqual(mode, "Standard")

    def test_handleCalculatorFocus_announces_mode_on_open(self):
        header = SimpleNamespace(name="Standard", UIAAutomationId="Header", children=[])
        calc_win = SimpleNamespace(
            name="Calculator",
            appModule=SimpleNamespace(appName="calculator"),
            windowHandle=5010,
            children=[header]
        )
        nvda_mocks.api._foreground = calc_win

        # First time opening calculator
        calculator.handleCalculatorFocus(calc_win)
        self.assertIn("Standard mode", nvda_mocks.ui.messages)

        # Subsequent focus within the same window should not repeat
        nvda_mocks.ui.messages.clear()
        calculator.handleCalculatorFocus(calc_win)
        self.assertEqual(len(nvda_mocks.ui.messages), 0, "Should not repeat within same window session")

        # A new window handle (e.g. calculator restarted)
        calc_win2 = SimpleNamespace(
            name="Calculator",
            appModule=SimpleNamespace(appName="calculator"),
            windowHandle=5011,
            children=[header]
        )
        nvda_mocks.api._foreground = calc_win2
        calculator.handleCalculatorFocus(calc_win2)
        self.assertIn("Standard mode", nvda_mocks.ui.messages)

    def test_AppModule_event_foreground(self):
        appMod = calculator.AppModule(100, "calculatorapp")
        header = SimpleNamespace(name="Standard", UIAAutomationId="Header", children=[])
        calc_win = SimpleNamespace(
            name="Calculator",
            appModule=appMod,
            windowHandle=6001,
            children=[header]
        )
        nvda_mocks.api._foreground = calc_win

        called = []
        def nextHandler():
            called.append(True)

        appMod.event_foreground(calc_win, nextHandler)
        self.assertEqual(len(called), 1)
        self.assertIn("Standard mode", nvda_mocks.ui.messages)

        # Repeating event_foreground on same window handle does not duplicate announcement
        nvda_mocks.ui.messages.clear()
        called.clear()
        appMod.event_foreground(calc_win, nextHandler)
        self.assertEqual(len(called), 1)
        self.assertEqual(len(nvda_mocks.ui.messages), 0)

    def test_AppModule_event_gainFocus(self):
        appMod = calculator.AppModule(100, "calculatorapp")
        header = SimpleNamespace(name="Scientific", UIAAutomationId="Header", children=[])
        calc_win = SimpleNamespace(
            name="Calculator",
            appModule=appMod,
            windowHandle=6002,
            children=[header]
        )
        nvda_mocks.api._foreground = calc_win

        called = []
        def nextHandler():
            called.append(True)

        appMod.event_gainFocus(calc_win, nextHandler)
        self.assertEqual(len(called), 1)
        self.assertIn("Scientific mode", nvda_mocks.ui.messages)

    def test_calculatorapp_module_aliases_calculator(self):
        self.assertIs(calculatorapp.AppModule, calculator.AppModule)


if __name__ == "__main__":
    unittest.main()
