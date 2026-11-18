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

from appModules import systemsettings as installed_apps
from types import SimpleNamespace


class TestInstalledApps(unittest.TestCase):
    def setUp(self):
        nvda_mocks.ui.messages.clear()
        installed_apps._lastAnnouncedAppsFound = None
        installed_apps._lastAnnouncedTime = 0.0

    def test_isSettingsApp(self):
        obj = SimpleNamespace(appModule=SimpleNamespace(appName="systemsettings"))
        self.assertTrue(installed_apps.isSettingsApp(obj))

        obj = SimpleNamespace(appModule=SimpleNamespace(appName="SystemSettings"))
        self.assertTrue(installed_apps.isSettingsApp(obj))

        # In an app module, any object routed here is treated as belonging to the app
        obj = SimpleNamespace(appModule=None)
        self.assertTrue(installed_apps.isSettingsApp(obj))

    def test_isDriveFilterComboBox(self):
        role_combo = nvda_mocks.controlTypes.Role.COMBOBOX
        role_list = nvda_mocks.controlTypes.Role.LIST

        # Combo box with name "Filter by drive"
        obj = SimpleNamespace(
            appModule=SimpleNamespace(appName="systemsettings"),
            role=role_combo,
            name="Filter by drive",
            UIAAutomationId=""
        )
        self.assertTrue(installed_apps.isDriveFilterComboBox(obj))

        # Combo box with "All drives"
        obj = SimpleNamespace(
            appModule=SimpleNamespace(appName="systemsettings"),
            role=role_combo,
            name="All drives",
            UIAAutomationId=""
        )
        self.assertTrue(installed_apps.isDriveFilterComboBox(obj))

        # "Sort by" combo box should return False
        obj = SimpleNamespace(
            appModule=SimpleNamespace(appName="systemsettings"),
            role=role_combo,
            name="Sort by",
            UIAAutomationId="SortByComboBox"
        )
        self.assertFalse(installed_apps.isDriveFilterComboBox(obj))

        # Not a combo box
        obj = SimpleNamespace(
            appModule=SimpleNamespace(appName="systemsettings"),
            role=role_list,
            name="Filter by drive",
            UIAAutomationId=""
        )
        self.assertFalse(installed_apps.isDriveFilterComboBox(obj))

    def test_findAppsFoundText(self):
        # Case 1: Previous sibling has "137 apps found"
        prev = SimpleNamespace(name="137 apps found")
        obj = SimpleNamespace(previous=prev, parent=None)
        self.assertEqual(installed_apps.findAppsFoundText(obj), "137 apps found")

        # Case 2: Sibling in parent container
        sibling = SimpleNamespace(name="24 apps found")
        parent = SimpleNamespace(children=[sibling], previous=None, parent=None)
        obj = SimpleNamespace(previous=None, parent=parent)
        self.assertEqual(installed_apps.findAppsFoundText(obj), "24 apps found")

        # Case 3: Uncle container (header container above filter row)
        header_text = SimpleNamespace(name="1 app found")
        header_container = SimpleNamespace(name="", children=[header_text])
        grandparent = SimpleNamespace(children=[header_container])
        parent = SimpleNamespace(children=[], previous=None, parent=grandparent)
        obj = SimpleNamespace(previous=None, parent=parent)
        self.assertEqual(installed_apps.findAppsFoundText(obj), "1 app found")

    def test_extractAppSize(self):
        # Case 1: Direct child with size in MB
        c1 = SimpleNamespace(name="350 MB", value="", children=[])
        obj = SimpleNamespace(children=[c1])
        self.assertEqual(installed_apps.extractAppSize(obj), "350 MB")

        # Case 2: Size in GB
        c2 = SimpleNamespace(name="1.52 GB", value="", children=[])
        obj = SimpleNamespace(children=[c2])
        self.assertEqual(installed_apps.extractAppSize(obj), "1.52 GB")

        # Case 3: Size in KB
        c3 = SimpleNamespace(name="16.0 KB", value="", children=[])
        obj = SimpleNamespace(children=[c3])
        self.assertEqual(installed_apps.extractAppSize(obj), "16.0 KB")

        # Case 4: Grandchild with size
        gc = SimpleNamespace(name="42.5 MB", value="", children=[])
        parent_c = SimpleNamespace(name="App Info", value="", children=[gc])
        obj = SimpleNamespace(children=[parent_c])
        self.assertEqual(installed_apps.extractAppSize(obj), "42.5 MB")

        # Case 5: Embedded size
        c5 = SimpleNamespace(name="Size: 120 MB", value="", children=[])
        obj = SimpleNamespace(children=[c5])
        self.assertEqual(installed_apps.extractAppSize(obj), "120 MB")

        # Case 6: Navigation via firstChild and next
        col1 = SimpleNamespace(name="AppName", value="", firstChild=None, next=None)
        col2 = SimpleNamespace(name="350 MB", value="", firstChild=None, next=None)
        col1.next = col2
        obj_linked = SimpleNamespace(children=[], firstChild=col1)
        self.assertEqual(installed_apps.extractAppSize(obj_linked), "350 MB")

        # Case 7: No size
        c7 = SimpleNamespace(name="Publisher: Microsoft", value="", children=[])
        obj = SimpleNamespace(children=[c7])
        self.assertIsNone(installed_apps.extractAppSize(obj))

    def test_isInstalledAppListItem(self):
        # LISTITEM
        parent = SimpleNamespace(role=nvda_mocks.controlTypes.Role.LIST, parent=None)
        obj1 = SimpleNamespace(
            appModule=SimpleNamespace(appName="systemsettings"),
            role=nvda_mocks.controlTypes.Role.LISTITEM,
            parent=parent,
            children=[]
        )
        self.assertTrue(installed_apps.isInstalledAppListItem(obj1))

        # TABLEROW (Windows 11 Settings table row)
        tbl_parent = SimpleNamespace(role=nvda_mocks.controlTypes.Role.TABLE, parent=None)
        obj2 = SimpleNamespace(
            appModule=SimpleNamespace(appName="systemsettings"),
            role=nvda_mocks.controlTypes.Role.TABLEROW,
            parent=tbl_parent,
            children=[]
        )
        self.assertTrue(installed_apps.isInstalledAppListItem(obj2))

    def test_InstalledAppItemOverlay_get_name(self):
        overlay = installed_apps.InstalledAppItemOverlay()
        overlay.name = "Google Chrome"
        c = SimpleNamespace(name="350 MB", value="", children=[])
        overlay.children = [c]

        self.assertEqual(overlay._get_name(), "Google Chrome, 350 MB")

        # If name already has size, do not duplicate
        overlay._appSize = None
        overlay.name = "Google Chrome, 350 MB"
        self.assertEqual(overlay._get_name(), "Google Chrome, 350 MB")

    def test_handleGainFocus_announces_apps_found(self):
        called = []
        def nextHandler():
            called.append(True)

        prev = SimpleNamespace(name="137 apps found")
        obj = SimpleNamespace(
            appModule=SimpleNamespace(appName="systemsettings"),
            role=nvda_mocks.controlTypes.Role.COMBOBOX,
            name="Filter by drive",
            previous=prev,
            parent=None
        )

        installed_apps.handleGainFocus(obj, nextHandler)
        self.assertEqual(len(called), 1, "nextHandler must be called")
        self.assertIn("137 apps found", nvda_mocks.ui.messages)

    def test_handleGainFocus_fallback_announces_size_if_missing_from_name(self):
        called = []
        def nextHandler():
            called.append(True)

        c = SimpleNamespace(name="512 MB", value="", children=[])
        obj = SimpleNamespace(
            appModule=SimpleNamespace(appName="systemsettings"),
            role=nvda_mocks.controlTypes.Role.LISTITEM,
            name="7-Zip 23.01",
            children=[c],
            parent=SimpleNamespace(role=nvda_mocks.controlTypes.Role.LIST)
        )

        nvda_mocks.ui.messages.clear()
        installed_apps.handleGainFocus(obj, nextHandler)
        self.assertEqual(len(called), 1)
        self.assertIn("512 MB", nvda_mocks.ui.messages)

    def test_AppModule_chooseNVDAObjectOverlayClasses(self):
        appMod = installed_apps.AppModule(101, "systemsettings")
        parent = SimpleNamespace(role=nvda_mocks.controlTypes.Role.LIST, parent=None)
        obj = nvda_mocks.BaseUIA(
            name="Mozilla Firefox",
            role=nvda_mocks.controlTypes.Role.LISTITEM,
            parent=parent,
            children=[SimpleNamespace(name="200 MB", value="", children=[])]
        )

        clsList = []
        appMod.chooseNVDAObjectOverlayClasses(obj, clsList)
        self.assertIn(installed_apps.InstalledAppItemOverlay, clsList)

    def test_AppModule_event_gainFocus(self):
        appMod = installed_apps.AppModule(101, "systemsettings")
        called = []
        def nextHandler():
            called.append(True)

        prev = SimpleNamespace(name="50 apps found")
        obj = SimpleNamespace(
            role=nvda_mocks.controlTypes.Role.COMBOBOX,
            name="Filter by drive",
            previous=prev,
            parent=None
        )

        nvda_mocks.ui.messages.clear()
        appMod.event_gainFocus(obj, nextHandler)
        self.assertEqual(len(called), 1)
        self.assertIn("50 apps found", nvda_mocks.ui.messages)


if __name__ == "__main__":
    unittest.main()
