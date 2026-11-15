# -*- coding: UTF-8 -*-
# search_context_menu.py
# Enhances Windows 11 Start Menu / Windows Search search result context menu navigation.
# Suppresses the repetitive "context menu list" announcement when navigating items with Up/Down arrows.

import time
import controlTypes
import winUser
import keyboardHandler
import inputCore
from logHandler import log
import NVDAObjects.UIA

# Track timestamp of the last detected Up or Down arrow key gesture
_lastArrowNavTime = 0.0

# Supported process/app names for Windows Search and Start Menu in Windows 11
SEARCH_APP_NAMES = {
    "searchhost",
    "searchui",
    "startmenuexperiencehost",
}

# Known context menu action item names (English and common variants)
KNOWN_MENU_ITEM_KEYWORDS = (
    "open",
    "run as administrator",
    "open file location",
    "pin to start",
    "pin to taskbar",
    "uninstall",
    "app settings",
    "copy",
    "properties",
)


def _onDecideExecuteGesture(gesture):
    """Tracks whether the current gesture is an Up or Down arrow key."""
    global _lastArrowNavTime
    try:
        vk = getattr(gesture, "vkCode", None)
        mainKeyName = getattr(gesture, "mainKeyName", "") or ""
        if vk in (winUser.VK_UP, winUser.VK_DOWN) or mainKeyName.lower() in ("uparrow", "downarrow", "up", "down"):
            _lastArrowNavTime = time.time()
    except Exception:
        pass
    return True


def isArrowNavigation():
    """Returns True if the current focus transition was triggered by Up or Down arrow key."""
    # Check 1: Recent gesture timestamp (within last 800ms)
    if (time.time() - _lastArrowNavTime) < 0.8:
        return True

    # Check 2: NVDA's keyboardHandler last passed-through key
    lastPass = getattr(keyboardHandler, "lastPassThroughKeyDown", None)
    if lastPass and isinstance(lastPass, tuple) and len(lastPass) >= 1:
        if lastPass[0] in (winUser.VK_UP, winUser.VK_DOWN):
            return True

    # Check 3: Check if arrow keys are physically down
    try:
        if (winUser.getKeyState(winUser.VK_UP) & 0x8000) or (winUser.getKeyState(winUser.VK_DOWN) & 0x8000):
            return True
    except Exception:
        pass

    return False


def isSearchApp(obj):
    """Determines whether the object belongs to Windows 11 Search or Start Menu."""
    if not obj:
        return False
    try:
        appModule = getattr(obj, "appModule", None)
        appName = (getattr(appModule, "appName", None) or "").lower()
        if appName in SEARCH_APP_NAMES:
            return True
    except Exception:
        pass
    return False


def isSearchContextMenuList(obj):
    """
    Checks if the object is the context menu list container for search results
    in Windows 11 Search / Start Menu.
    Safely avoids accessing UIA properties on non-UIA objects (such as Chromium IA2 objects).
    """
    try:
        if not obj:
            return False
        if not isSearchApp(obj):
            return False

        # Check role: In Windows 11 Search (Chromium/IA2 or XAML), the context menu is a List or PopupMenu
        role = getattr(obj, "role", None)
        if role not in (
            controlTypes.Role.LIST,
            controlTypes.Role.POPUPMENU,
            controlTypes.Role.MENU,
        ):
            roleText = (getattr(obj, "roleText", "") or "").lower()
            if roleText not in ("list", "menu", "context menu"):
                return False

        name = (getattr(obj, "name", "") or "").lower()

        # In Windows Search, the context menu list container is named "context menu"
        if "context menu" in name or "contextmenu" in name:
            return True

        # Only query UIAAutomationId if obj is an authentic UIA NVDAObject
        if isinstance(obj, getattr(NVDAObjects.UIA, "UIA", tuple())):
            try:
                autoId = (getattr(obj, "UIAAutomationId", "") or "").lower()
                if any(k in autoId for k in ("menuflyout", "contextflyout", "contextmenu", "flyout", "popup")):
                    return True
            except Exception:
                pass

        # Inspect children to see if they are context menu items (e.g. Open, Run as administrator)
        try:
            children = getattr(obj, "children", []) or []
            for child in children[:6]:
                cname = (getattr(child, "name", "") or "").lower()
                if any(action in cname for action in KNOWN_MENU_ITEM_KEYWORDS):
                    return True
        except Exception:
            pass

    except Exception:
        pass

    return False


def handleFocusEntered(obj, nextHandler):
    """
    Called from GlobalPlugin.event_focusEntered.
    If the entering ancestor is the Windows Search context menu list and the user
    navigated using Up or Down arrow, suppresses the repetitive 'context menu list' announcement.
    """
    try:
        if isSearchContextMenuList(obj) and isArrowNavigation():
            log.debug("win11_access: Suppressed 'context menu list' announcement on arrow navigation")
            return
    except Exception as e:
        log.error(f"win11_access: Error in handleFocusEntered: {e}")

    nextHandler()


def chooseNVDAObjectOverlayClasses(obj, clsList):
    """No overlay class is needed; focusEntered suppression handles context menu cleanly."""
    pass


def register():
    """Registers input hooks for tracking arrow navigation."""
    try:
        inputCore.decide_executeGesture.register(_onDecideExecuteGesture)
    except Exception as e:
        log.error(f"win11_access: Failed to register decide_executeGesture hook: {e}")


def unregister():
    """Unregisters input hooks."""
    try:
        inputCore.decide_executeGesture.unregister(_onDecideExecuteGesture)
    except Exception as e:
        log.error(f"win11_access: Failed to unregister decide_executeGesture hook: {e}")
