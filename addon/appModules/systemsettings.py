# -*- coding: UTF-8 -*-
# systemsettings.py
# NVDA App Module for Windows 11 Settings (SystemSettings.exe)
# Part of win11_access add-on.
# Author: Bibek Sharma Dhakal
#
# Enhancements for Windows 11 Settings -> Apps -> Installed apps:
# 1. Announces the number of apps found (e.g. "137 apps found") when focusing the drive filter combo box.
# 2. Announces the application size (e.g. "350 MB") when navigating the installed applications list.

import re
import time
import controlTypes
import ui
from logHandler import log
import NVDAObjects.UIA
import appModuleHandler

try:
    from nvdaBuiltin.appModules.systemsettings import AppModule as BuiltInAppModule
except ImportError:
    BuiltInAppModule = appModuleHandler.AppModule

# Regex pattern to match "X apps found" (supporting various localized variants)
APPS_FOUND_PATTERN = re.compile(
    r"\b(\d+\s+(?:apps?|applications?|Programme?|éléments?|elementos|aplicaciones|applicazioni)\s*(?:found|trouvés?|trouvées?|gefunden|encontrados?|encontradas?|trovati|trovate)?)\b",
    re.IGNORECASE,
)

# Regex pattern for standalone app storage size strings (e.g. "350 MB", "1.25 GB", "45 KB", "100 bytes")
SIZE_REGEX = re.compile(
    r"^\s*(\d+(?:[\.,]\d+)?\s*(?:bytes?|byte|B|KB|MB|GB|TB|PB|Ko|Mo|Go|To|КБ|МБ|ГБ|ТБ))\s*$",
    re.IGNORECASE,
)

# Regex pattern for size embedded within other text (e.g. "Size: 350 MB")
EMBEDDED_SIZE_REGEX = re.compile(
    r"\b(\d+(?:[\.,]\d+)?\s*(?:bytes?|byte|KB|MB|GB|TB|PB|Ko|Mo|Go|To|КБ|МБ|ГБ|ТБ))\b",
    re.IGNORECASE,
)


def isSettingsApp(obj):
    """Checks whether the object belongs to Windows Settings (SystemSettings.exe)."""
    if not obj:
        return False
    try:
        appModule = getattr(obj, "appModule", None)
        appName = (getattr(appModule, "appName", None) or "").lower()
        if appName == "systemsettings":
            return True
        # If in an app module, the object belongs to this app
        return True
    except Exception:
        return True


def isDriveFilterComboBox(obj):
    """
    Checks whether the object is the drive filter combo box in Installed apps.
    Usually named "Filter by drive", "All drives", "Drive", or has automation ID
    containing "drive" or "filter".
    """
    try:
        if getattr(obj, "role", None) != controlTypes.Role.COMBOBOX:
            return False

        name = (getattr(obj, "name", "") or "").lower()
        autoId = ""
        if isinstance(obj, getattr(NVDAObjects.UIA, "UIA", tuple())):
            try:
                autoId = (getattr(obj, "UIAAutomationId", "") or "").lower()
            except Exception:
                autoId = ""

        if any(k in name for k in ("drive", "drives", "all drives")):
            return True
        if any(k in autoId for k in ("drive", "filterbydrive", "drivefilter")):
            return True
        if "filter" in name and "sort" not in name:
            return True
    except Exception:
        pass

    return False


def findAppsFoundText(obj):
    """
    Locates the "X apps found" text element located near the drive filter combo box.
    Inspects previous siblings, parent siblings, and nearby containers.
    """
    # 1. Check previous element directly
    try:
        prev = getattr(obj, "previous", None)
        if prev:
            pname = getattr(prev, "name", "") or ""
            m = APPS_FOUND_PATTERN.search(pname)
            if m:
                return m.group(1).strip()
    except Exception:
        pass

    # 2. Check siblings in the same container
    try:
        parent = getattr(obj, "parent", None)
        if parent:
            for sibling in getattr(parent, "children", []) or []:
                if sibling != obj:
                    sname = getattr(sibling, "name", "") or ""
                    m = APPS_FOUND_PATTERN.search(sname)
                    if m:
                        return m.group(1).strip()

            # 3. Check previous container (the header row above filter controls)
            prevParent = getattr(parent, "previous", None)
            if prevParent:
                ppname = getattr(prevParent, "name", "") or ""
                m = APPS_FOUND_PATTERN.search(ppname)
                if m:
                    return m.group(1).strip()
                for child in getattr(prevParent, "children", []) or []:
                    cname = getattr(child, "name", "") or ""
                    m = APPS_FOUND_PATTERN.search(cname)
                    if m:
                        return m.group(1).strip()

            # 4. Check grandparent level siblings/children
            grandParent = getattr(parent, "parent", None)
            if grandParent:
                for uncle in getattr(grandParent, "children", []) or []:
                    if uncle != parent:
                        uname = getattr(uncle, "name", "") or ""
                        m = APPS_FOUND_PATTERN.search(uname)
                        if m:
                            return m.group(1).strip()
                        for child in getattr(uncle, "children", []) or []:
                            cname = getattr(child, "name", "") or ""
                            m = APPS_FOUND_PATTERN.search(cname)
                            if m:
                                return m.group(1).strip()
    except Exception:
        pass

    return None


def extractAppSize(obj):
    """
    Extracts the application size (e.g. "350 MB", "1.25 GB") from an installed app list item.
    Inspects descendants via breadth-first search as well as firstChild/next navigation.
    """
    if not obj:
        return None

    # Strategy 1: Breadth-first search of children and grandchildren up to depth 3
    queue = [(obj, 0)]
    visited = set()
    while queue:
        curr, depth = queue.pop(0)
        currId = id(curr)
        if currId in visited:
            continue
        visited.add(currId)

        if depth > 0:
            for attr in ("name", "value", "description", "displayText"):
                try:
                    val = getattr(curr, attr, "") or ""
                    if isinstance(val, str) and val.strip():
                        valClean = val.strip()
                        m = SIZE_REGEX.match(valClean)
                        if m:
                            return m.group(1).strip()
                        m = EMBEDDED_SIZE_REGEX.search(valClean)
                        if m:
                            return m.group(1).strip()
                except Exception:
                    pass

        if depth < 3:
            try:
                for child in getattr(curr, "children", []) or []:
                    queue.append((child, depth + 1))
            except Exception:
                pass

    # Strategy 2: Walk firstChild and next siblings
    try:
        curr = getattr(obj, "firstChild", None)
        count = 0
        while curr and count < 25:
            for attr in ("name", "value", "description", "displayText"):
                try:
                    val = getattr(curr, attr, "") or ""
                    if isinstance(val, str) and val.strip():
                        valClean = val.strip()
                        m = SIZE_REGEX.match(valClean) or EMBEDDED_SIZE_REGEX.search(valClean)
                        if m:
                            return m.group(1).strip()
                except Exception:
                    pass

            # Also check child of this column/cell
            try:
                cellChild = getattr(curr, "firstChild", None)
                if cellChild:
                    for attr in ("name", "value", "description", "displayText"):
                        val = getattr(cellChild, attr, "") or ""
                        if isinstance(val, str) and val.strip():
                            valClean = val.strip()
                            m = SIZE_REGEX.match(valClean) or EMBEDDED_SIZE_REGEX.search(valClean)
                            if m:
                                return m.group(1).strip()
            except Exception:
                pass

            curr = getattr(curr, "next", None)
            count += 1
    except Exception:
        pass

    return None


class InstalledAppItemOverlay(NVDAObjects.UIA.UIA):
    """
    Overlay class for installed app items in Windows 11 Settings.
    Appends the application size to the object's name so NVDA speaks and brailles
    it automatically while navigating the list.
    """

    _appSize = None

    def _get_name(self):
        try:
            baseName = super()._get_name() or ""
        except Exception:
            baseName = getattr(self, "_name", "") or ""

        try:
            if self._appSize is None:
                self._appSize = extractAppSize(self) or ""
            if self._appSize and self._appSize not in baseName:
                return f"{baseName}, {self._appSize}"
        except Exception:
            pass

        return baseName

    def _get_description(self):
        try:
            baseDesc = super()._get_description() or ""
        except Exception:
            baseDesc = getattr(self, "_description", "") or ""

        try:
            if self._appSize is None:
                self._appSize = extractAppSize(self) or ""
            baseName = getattr(self, "name", "") or ""
            if self._appSize and self._appSize not in baseDesc and self._appSize not in baseName:
                if baseDesc:
                    return f"{baseDesc}, {self._appSize}"
                return self._appSize
        except Exception:
            pass

        return baseDesc


def isInstalledAppListItem(obj):
    """
    Checks whether the object represents an item in the Windows 11 installed apps list.
    Safely uses valid NVDA controlTypes.Role enum values.
    """
    try:
        role = getattr(obj, "role", None)
        validRoles = (
            controlTypes.Role.LISTITEM,
            controlTypes.Role.DATAITEM,
            getattr(controlTypes.Role, "TABLEROW", None),
        )
        if role not in validRoles:
            return False

        # Check parent/ancestor
        parent = getattr(obj, "parent", None)
        if parent:
            parentRole = getattr(parent, "role", None)
            parentAutoId = ""
            if isinstance(parent, getattr(NVDAObjects.UIA, "UIA", tuple())):
                try:
                    parentAutoId = (getattr(parent, "UIAAutomationId", "") or "").lower()
                except Exception:
                    parentAutoId = ""

            validParentRoles = (
                controlTypes.Role.LIST,
                controlTypes.Role.TABLE,
                controlTypes.Role.DATAGRID,
                getattr(controlTypes.Role, "TABLEBODY", None),
            )
            if parentRole in validParentRoles:
                if not parentAutoId or any(k in parentAutoId for k in ("app", "install", "features", "list")):
                    return True

        # If size can be extracted, it is definitely an installed app item
        if extractAppSize(obj):
            return True

    except Exception:
        pass

    return False


class AppModule(BuiltInAppModule):
    """
    App module for Windows Settings (SystemSettings.exe).
    Enhancements for Windows 11 Settings -> Apps -> Installed apps:
    - Automatically announces 'X apps found' when focusing the drive filter combo box.
    - Automatically announces application size while navigating the installed apps list.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lastAnnouncedAppsFound = None
        self._lastAnnouncedTime = 0.0

    def chooseNVDAObjectOverlayClasses(self, obj, clsList):
        """Applies InstalledAppItemOverlay to installed app items."""
        if hasattr(super(), "chooseNVDAObjectOverlayClasses"):
            super().chooseNVDAObjectOverlayClasses(obj, clsList)
        try:
            if isinstance(obj, getattr(NVDAObjects.UIA, "UIA", tuple())):
                if isInstalledAppListItem(obj):
                    clsList.insert(0, InstalledAppItemOverlay)
        except Exception as e:
            log.error(f"win11_access: Error in systemsettings chooseNVDAObjectOverlayClasses: {e}")

    def event_gainFocus(self, obj, nextHandler):
        """
        Handles focus gain in Windows Settings:
        - If focused control is drive filter combo box, announces 'X apps found'.
        - If focused control is an installed app item, ensures app size is announced.
        """
        if hasattr(super(), "event_gainFocus"):
            super().event_gainFocus(obj, nextHandler)
        else:
            nextHandler()

        try:
            if isDriveFilterComboBox(obj):
                appsCountText = findAppsFoundText(obj)
                now = time.time()
                if appsCountText:
                    if appsCountText != self._lastAnnouncedAppsFound or (now - self._lastAnnouncedTime) > 1.0:
                        self._lastAnnouncedAppsFound = appsCountText
                        self._lastAnnouncedTime = now
                        ui.message(appsCountText)
            elif isInstalledAppListItem(obj):
                # Fallback announcement: If overlay wasn't applied or name doesn't contain size yet, speak it
                size = extractAppSize(obj)
                if size:
                    baseName = getattr(obj, "name", "") or ""
                    if size not in baseName:
                        ui.message(size)
        except Exception as e:
            log.error(f"win11_access: Error in systemsettings event_gainFocus: {e}")


# Module-level convenience functions for backwards compatibility and direct invocation
_moduleInstance = None

def _getModuleInstance():
    global _moduleInstance
    if _moduleInstance is None:
        _moduleInstance = AppModule(0, "systemsettings")
    return _moduleInstance

def chooseNVDAObjectOverlayClasses(obj, clsList):
    _getModuleInstance().chooseNVDAObjectOverlayClasses(obj, clsList)

def handleGainFocus(obj, nextHandler):
    _getModuleInstance().event_gainFocus(obj, nextHandler)
