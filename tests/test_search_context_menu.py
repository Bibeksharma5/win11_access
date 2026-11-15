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

from globalPlugins.win11_access import search_context_menu
from types import SimpleNamespace


class TestSearchContextMenu(unittest.TestCase):
    def setUp(self):
        nvda_mocks.keyboardHandler.lastPassThroughKeyDown = None
        search_context_menu._lastArrowNavTime = 0.0

    def test_isSearchApp(self):
        obj = SimpleNamespace(appModule=SimpleNamespace(appName="searchhost"))
        self.assertTrue(search_context_menu.isSearchApp(obj))

        obj = SimpleNamespace(appModule=SimpleNamespace(appName="SearchUI"))
        self.assertTrue(search_context_menu.isSearchApp(obj))

        obj = SimpleNamespace(appModule=SimpleNamespace(appName="StartMenuExperienceHost"))
        self.assertTrue(search_context_menu.isSearchApp(obj))

        obj = SimpleNamespace(appModule=SimpleNamespace(appName="explorer"))
        self.assertFalse(search_context_menu.isSearchApp(obj))

        obj = SimpleNamespace(appModule=None)
        self.assertFalse(search_context_menu.isSearchApp(obj))

    def test_isSearchContextMenuList(self):
        role_list = nvda_mocks.controlTypes.Role.LIST

        # Context menu in searchhost with "context menu" in name
        obj = SimpleNamespace(
            appModule=SimpleNamespace(appName="searchhost"),
            role=role_list,
            name="context menu",
            UIAAutomationId="",
            children=[]
        )
        self.assertTrue(search_context_menu.isSearchContextMenuList(obj))

        # Context menu with children containing "Run as administrator"
        child = SimpleNamespace(name="Run as administrator")
        obj = SimpleNamespace(
            appModule=SimpleNamespace(appName="searchhost"),
            role=role_list,
            name="",
            children=[child]
        )
        self.assertTrue(search_context_menu.isSearchContextMenuList(obj))

        # Non-UIA object should not crash when UIAAutomationId is absent
        obj_ia2 = SimpleNamespace(
            appModule=SimpleNamespace(appName="searchhost"),
            role=role_list,
            name="context menu",
            children=[]
        )
        self.assertTrue(search_context_menu.isSearchContextMenuList(obj_ia2))

        # Context menu in another app (e.g. explorer) should return False
        obj_other = SimpleNamespace(
            appModule=SimpleNamespace(appName="explorer"),
            role=role_list,
            name="context menu",
            children=[]
        )
        self.assertFalse(search_context_menu.isSearchContextMenuList(obj_other))

    def test_chooseNVDAObjectOverlayClasses_does_not_modify_clsList(self):
        # Must not inject UIA overlay into clsList for Chromium IA2 objects
        obj = SimpleNamespace(
            appModule=SimpleNamespace(appName="searchhost"),
            role=nvda_mocks.controlTypes.Role.LIST,
            name="context menu"
        )
        clsList = []
        search_context_menu.chooseNVDAObjectOverlayClasses(obj, clsList)
        self.assertEqual(len(clsList), 0, "Overlay classes must not be inserted into search context menu")

    def test_isArrowNavigation(self):
        # Default state
        self.assertFalse(search_context_menu.isArrowNavigation())

        # Up arrow pressed
        nvda_mocks.keyboardHandler.lastPassThroughKeyDown = (nvda_mocks.winUser.VK_UP, False)
        self.assertTrue(search_context_menu.isArrowNavigation())

        # Down arrow pressed
        nvda_mocks.keyboardHandler.lastPassThroughKeyDown = (nvda_mocks.winUser.VK_DOWN, False)
        self.assertTrue(search_context_menu.isArrowNavigation())

        # Other key pressed (e.g. Apps key = 93)
        nvda_mocks.keyboardHandler.lastPassThroughKeyDown = (93, False)
        self.assertFalse(search_context_menu.isArrowNavigation())

    def test_handleFocusEntered_suppresses_only_on_arrow_in_search(self):
        called = []
        def mockNextHandler():
            called.append(True)

        obj_search = SimpleNamespace(
            appModule=SimpleNamespace(appName="searchhost"),
            role=nvda_mocks.controlTypes.Role.LIST,
            name="context menu",
            children=[]
        )

        obj_other = SimpleNamespace(
            appModule=SimpleNamespace(appName="explorer"),
            role=nvda_mocks.controlTypes.Role.LIST,
            name="context menu",
            children=[]
        )

        # Case 1: In search context menu, user presses Down arrow -> SUPPRESSED (nextHandler NOT called)
        nvda_mocks.keyboardHandler.lastPassThroughKeyDown = (nvda_mocks.winUser.VK_DOWN, False)
        called.clear()
        search_context_menu.handleFocusEntered(obj_search, mockNextHandler)
        self.assertEqual(len(called), 0, "nextHandler must be suppressed during arrow navigation in search context menu")

        # Case 2: In search context menu, user opened menu via Apps key (93) -> NOT suppressed (nextHandler called)
        nvda_mocks.keyboardHandler.lastPassThroughKeyDown = (93, False)
        called.clear()
        search_context_menu.handleFocusEntered(obj_search, mockNextHandler)
        self.assertEqual(len(called), 1, "nextHandler must be called when context menu first opens via apps key")

        # Case 3: In explorer context menu, user presses Down arrow -> NOT suppressed (other menus unaffected)
        nvda_mocks.keyboardHandler.lastPassThroughKeyDown = (nvda_mocks.winUser.VK_DOWN, False)
        called.clear()
        search_context_menu.handleFocusEntered(obj_other, mockNextHandler)
        self.assertEqual(len(called), 1, "nextHandler must be called for non-search context menus")


if __name__ == "__main__":
    unittest.main()
