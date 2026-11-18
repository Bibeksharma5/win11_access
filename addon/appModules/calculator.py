# -*- coding: UTF-8 -*-
# calculator.py
# NVDA App Module for Windows Calculator (CalculatorApp.exe, Calculator.exe, calc.exe)
# Part of win11_access add-on.
# Author: Bibek Sharma Dhakal
#
# Enhancements for Windows Calculator:
# Announces the currently active calculation mode (e.g. Standard mode, Scientific mode,
# Programmer mode) immediately upon opening or switching to the Calculator application,
# without sluggishness or delay.

import api
import core
import ui
import winUser
from logHandler import log
import NVDAObjects.UIA
import appModuleHandler

try:
    from nvdaBuiltin.appModules.calculator import AppModule as BuiltInAppModule
except ImportError:
    BuiltInAppModule = appModuleHandler.AppModule

# Global fallback set of calculator window handles (HWNDs) that have already had their mode announced
_announcedCalculatorHwnds = set()

# Known calculation modes in Windows 11 Calculator
KNOWN_CALCULATOR_MODES = (
    "Standard",
    "Scientific",
    "Programmer",
    "Graphing",
    "Date Calculation",
    "Currency",
    "Volume",
    "Length",
    "Weight and Mass",
    "Temperature",
    "Energy",
    "Area",
    "Speed",
    "Time",
    "Power",
    "Data",
    "Pressure",
    "Angle",
)

CALCULATOR_APP_NAMES = {
    "calculator",
    "calculatorapp",
    "calc",
    "windowscalculator",
}

HEADER_AUTOMATION_IDS = {
    "header",
    "headertitletext",
    "normalheader",
    "staticheader",
    "titlecontentcontrol",
    "navviewheader",
}


def _extractModeFromText(text):
    """
    Extracts a known calculation mode from a string if present.
    Handles 'Standard - Calculator', 'Standard Calculator', 'Standard mode', etc.
    Returns the mode string or None.
    """
    if not text or not isinstance(text, str):
        return None
    textClean = text.strip()
    if not textClean:
        return None
    textLower = textClean.lower()

    # Check "Mode - Calculator" or "Calculator - Mode"
    if " - " in textClean:
        for part in textClean.split(" - "):
            partClean = part.strip()
            partLower = partClean.lower()
            for mode in KNOWN_CALCULATOR_MODES:
                if partLower == mode.lower() or partLower == f"{mode.lower()} calculator" or partLower == f"{mode.lower()} mode":
                    return mode

    # Check exact match or "Standard Calculator" / "Standard mode"
    for mode in KNOWN_CALCULATOR_MODES:
        modeLower = mode.lower()
        if textLower == modeLower:
            return mode
        if textLower == f"{modeLower} calculator" or textLower == f"calculator {modeLower}":
            return mode
        if textLower == f"{modeLower} mode":
            return mode

    # Check if string starts with "<Mode> "
    for mode in KNOWN_CALCULATOR_MODES:
        modeLower = mode.lower()
        if textLower.startswith(f"{modeLower} "):
            return mode

    return None


def isCalculatorApp(obj):
    """
    Checks whether the object belongs to Windows Calculator.
    Accurately handles modern Windows 11 UWP/WinUI Calculator hosted in ApplicationFrameHost.exe.
    """
    if not obj:
        return False
    try:
        appModule = getattr(obj, "appModule", None)
        appName = (getattr(appModule, "appName", None) or "").lower()

        if appName in CALCULATOR_APP_NAMES:
            return True

        if appName == "applicationframehost":
            name = (getattr(obj, "name", "") or "").lower()
            if "calculator" in name or "calc" in name:
                return True
            hwnd = getattr(obj, "windowHandle", None)
            if hwnd:
                try:
                    wText = (winUser.getWindowText(hwnd) or "").lower()
                    if "calculator" in wText or "calc" in wText:
                        return True
                except Exception:
                    pass

        # Also check if object's window text matches calculator
        hwnd = getattr(obj, "windowHandle", None)
        if hwnd:
            try:
                wText = (winUser.getWindowText(hwnd) or "").lower()
                if "calculator" in wText:
                    return True
            except Exception:
                pass
    except Exception:
        pass

    return False


def getRootCalculatorHwnd(obj):
    """Returns the top-level HWND for the Calculator window."""
    hwnd = getattr(obj, "windowHandle", None)
    if not hwnd:
        return None
    try:
        rootHwnd = winUser.getAncestor(hwnd, winUser.GA_ROOT)
        return rootHwnd or hwnd
    except Exception:
        return hwnd


def _findElementByAutoId(root, targetAutoId, maxDepth=8):
    """Breadth-first search for a child element matching targetAutoId."""
    if not root:
        return None
    queue = [(root, 0)]
    targetLower = targetAutoId.lower()
    visited = set()

    while queue:
        curr, depth = queue.pop(0)
        currId = id(curr)
        if currId in visited:
            continue
        visited.add(currId)

        currAutoId = ""
        try:
            currAutoId = (getattr(curr, "UIAAutomationId", "") or "").lower()
        except Exception:
            currAutoId = ""

        if currAutoId == targetLower:
            return curr

        if depth < maxDepth:
            try:
                for child in getattr(curr, "children", []) or []:
                    queue.append((child, depth + 1))
            except Exception:
                pass
    return None


def _findKnownModeInDescendants(root, maxDepth=8):
    """Searches descendants for text elements matching a known calculator mode name."""
    if not root:
        return None
    queue = [(root, 0)]
    visited = set()

    while queue:
        curr, depth = queue.pop(0)
        currId = id(curr)
        if currId in visited:
            continue
        visited.add(currId)

        for attr in ("name", "displayText", "value"):
            try:
                currName = (getattr(curr, attr, "") or "").strip()
                if not currName:
                    continue
                mode = _extractModeFromText(currName)
                if mode:
                    return mode
            except Exception:
                pass

        if depth < maxDepth:
            try:
                for child in getattr(curr, "children", []) or []:
                    queue.append((child, depth + 1))
            except Exception:
                pass
    return None


def _findModeInTree(root, maxDepth=4):
    """
    Fast, single-pass breadth-first search for Calculator mode.
    Inspects element names, values, and AutomationIds in one shallow traversal.
    """
    if not root:
        return None

    queue = [(root, 0)]
    visited = set()

    while queue:
        curr, depth = queue.pop(0)
        currId = id(curr)
        if currId in visited:
            continue
        visited.add(currId)

        # Check AutomationId
        currAutoId = ""
        try:
            currAutoId = (getattr(curr, "UIAAutomationId", "") or "").lower()
        except Exception:
            currAutoId = ""

        # If element is a known header container, check its name or value
        if currAutoId in HEADER_AUTOMATION_IDS:
            for attr in ("name", "displayText", "value"):
                try:
                    val = (getattr(curr, attr, "") or "").strip()
                    mode = _extractModeFromText(val)
                    if mode:
                        return mode
                    if val and val in KNOWN_CALCULATOR_MODES:
                        return val
                except Exception:
                    pass

        # Check if element's name/text matches a known mode
        for attr in ("name", "displayText", "value"):
            try:
                val = (getattr(curr, attr, "") or "").strip()
                if val:
                    mode = _extractModeFromText(val)
                    if mode:
                        return mode
            except Exception:
                pass

        if depth < maxDepth:
            try:
                for child in getattr(curr, "children", []) or []:
                    queue.append((child, depth + 1))
            except Exception:
                pass

    return None


def getCalculatorMode(obj=None):
    """
    Attempts to identify the currently active calculation mode in Calculator.
    Checks candidate objects (passed obj, focusObject, foregroundObject),
    window titles, and fast shallow descendant searches.
    Returns mode name string if found, otherwise None.
    """
    candidates = []

    if obj and isCalculatorApp(obj):
        candidates.append(obj)

    focusObj = api.getFocusObject()
    if focusObj and isCalculatorApp(focusObj) and focusObj not in candidates:
        candidates.append(focusObj)

    fg = api.getForegroundObject()
    if fg and isCalculatorApp(fg) and fg not in candidates:
        candidates.append(fg)

    if not candidates and fg:
        # Check if foreground window title indicates Calculator
        hwnd = getattr(fg, "windowHandle", None)
        if hwnd:
            try:
                wText = (winUser.getWindowText(hwnd) or "").lower()
                if "calculator" in wText:
                    candidates.append(fg)
            except Exception:
                pass

    if not candidates:
        return None

    # Step 1: Immediate check on candidate names and window titles (0 ms)
    for root in candidates:
        for attr in ("name", "displayText", "value"):
            try:
                val = getattr(root, attr, "") or ""
                mode = _extractModeFromText(val)
                if mode:
                    return mode
            except Exception:
                pass

        hwnd = getattr(root, "windowHandle", None)
        if hwnd:
            try:
                title = winUser.getWindowText(hwnd) or ""
                mode = _extractModeFromText(title)
                if mode:
                    return mode
            except Exception:
                pass

    # Step 2: Immediate check on parents/ancestors up to 4 levels
    for root in candidates:
        curr = root
        for _ in range(4):
            p = getattr(curr, "parent", None)
            if not p:
                break
            for attr in ("name", "displayText", "value"):
                try:
                    val = getattr(p, attr, "") or ""
                    mode = _extractModeFromText(val)
                    if mode:
                        return mode
                except Exception:
                    pass
            hwnd = getattr(p, "windowHandle", None)
            if hwnd:
                try:
                    title = winUser.getWindowText(hwnd) or ""
                    mode = _extractModeFromText(title)
                    if mode:
                        return mode
                except Exception:
                    pass
            curr = p

    # Step 3: Fast single-pass shallow search (depth <= 4) from top containers
    visitedContainers = set()
    for root in candidates:
        top = root
        curr = root
        for _ in range(5):
            p = getattr(curr, "parent", None)
            if not p:
                break
            top = p
            curr = p

        for searchRoot in (top, root):
            rootId = id(searchRoot)
            if rootId in visitedContainers:
                continue
            visitedContainers.add(rootId)

            mode = _findModeInTree(searchRoot, maxDepth=4)
            if mode:
                return mode

    # Step 4: Fallback search for AutomationId "Header" / "HeaderTitleText" if deep
    for root in candidates:
        for headerId in ("Header", "HeaderTitleText", "NormalHeader"):
            header = _findElementByAutoId(root, headerId, maxDepth=8)
            if header:
                name = getattr(header, "name", "") or ""
                if name and name.strip():
                    return name.strip()

    return None


def _announceModeCallback(rootHwnd, retryCount=0, obj=None):
    """Callback function to announce Calculator mode, with fast short retries if needed."""
    mode = getCalculatorMode(obj)
    if mode:
        if "mode" in mode.lower() or "calculator" in mode.lower():
            message = mode
        else:
            message = f"{mode} mode"
        ui.message(message)
        log.info(f"win11_access: Announced Calculator mode: {message}")
    elif retryCount < 4:
        # Fast retry with minimal 50ms interval if WinUI 3 XAML island is still rendering
        core.callLater(50, lambda: _announceModeCallback(rootHwnd, retryCount + 1, obj))


def handleCalculatorFocus(obj):
    """
    Called on focus or foreground events.
    Detects if this is a newly opened Calculator window and announces active mode immediately.
    """
    global _announcedCalculatorHwnds
    if not isCalculatorApp(obj):
        fg = api.getForegroundObject()
        if not isCalculatorApp(fg):
            return

    rootHwnd = getRootCalculatorHwnd(obj)
    if not rootHwnd:
        fg = api.getForegroundObject()
        rootHwnd = getRootCalculatorHwnd(fg)

    if not rootHwnd:
        return

    if rootHwnd not in _announcedCalculatorHwnds:
        # Check immediately without artificial delay
        mode = getCalculatorMode(obj)
        if mode:
            _announcedCalculatorHwnds.add(rootHwnd)
            if "mode" in mode.lower() or "calculator" in mode.lower():
                message = mode
            else:
                message = f"{mode} mode"
            ui.message(message)
            log.info(f"win11_access: Announced Calculator mode: {message}")
            return

        _announcedCalculatorHwnds.add(rootHwnd)
        try:
            _announcedCalculatorHwnds = {h for h in _announcedCalculatorHwnds if winUser.isWindow(h)}
        except Exception:
            pass

        # Schedule quick retry (50ms) only if not ready yet
        core.callLater(50, lambda: _announceModeCallback(rootHwnd, 0, obj))


class AppModule(BuiltInAppModule):
    """
    App module for Windows Calculator.
    Announces the active calculation mode (Standard, Scientific, Programmer, etc.)
    immediately upon opening or switching to the application.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._announcedHwnds = set()
        self._pendingHwnds = set()

    def event_foreground(self, obj, nextHandler):
        """Called when Calculator window comes to foreground."""
        if hasattr(super(), "event_foreground"):
            super().event_foreground(obj, nextHandler)
        else:
            nextHandler()
        try:
            self._handleAppFocus(obj)
        except Exception as e:
            log.error(f"win11_access: Error in calculator event_foreground: {e}")

    def event_gainFocus(self, obj, nextHandler):
        """Called when an element in Calculator gains focus."""
        if hasattr(super(), "event_gainFocus"):
            super().event_gainFocus(obj, nextHandler)
        else:
            nextHandler()
        try:
            self._handleAppFocus(obj)
        except Exception as e:
            log.error(f"win11_access: Error in calculator event_gainFocus: {e}")

    def _speakMode(self, mode):
        """Speaks the active mode message."""
        if "mode" in mode.lower() or "calculator" in mode.lower():
            message = mode
        else:
            message = f"{mode} mode"
        ui.message(message)
        log.info(f"win11_access: Announced Calculator mode: {message}")

    def _handleAppFocus(self, obj):
        rootHwnd = getRootCalculatorHwnd(obj) or getattr(obj, "windowHandle", None)
        if not rootHwnd:
            fg = api.getForegroundObject()
            rootHwnd = getRootCalculatorHwnd(fg) or getattr(fg, "windowHandle", None)

        if not rootHwnd:
            return

        if rootHwnd in self._announcedHwnds:
            return

        # Clean up stale window handles
        try:
            self._announcedHwnds = {h for h in self._announcedHwnds if winUser.isWindow(h)}
        except Exception:
            pass

        # Fast path: Attempt immediate detection without delay (0 ms)
        mode = getCalculatorMode(obj)
        if mode:
            self._pendingHwnds.discard(rootHwnd)
            self._announcedHwnds.add(rootHwnd)
            self._speakMode(mode)
            return

        # Slow path: Schedule quick 50ms retry only if UI elements are still rendering
        if rootHwnd not in self._pendingHwnds:
            self._pendingHwnds.add(rootHwnd)
            core.callLater(50, lambda: self._announceMode(rootHwnd, 1, obj))

    def _announceMode(self, rootHwnd, retryCount=0, obj=None):
        if rootHwnd in self._announcedHwnds:
            self._pendingHwnds.discard(rootHwnd)
            return

        mode = getCalculatorMode(obj)
        if mode:
            self._pendingHwnds.discard(rootHwnd)
            self._announcedHwnds.add(rootHwnd)
            self._speakMode(mode)
        elif retryCount < 4:
            core.callLater(50, lambda: self._announceMode(rootHwnd, retryCount + 1, obj))
        else:
            self._pendingHwnds.discard(rootHwnd)


def handleForeground(obj, nextHandler):
    """Backward compatibility helper."""
    nextHandler()
    try:
        handleCalculatorFocus(obj)
    except Exception as e:
        log.error(f"win11_access: Error in calculator handleForeground: {e}")


def handleGainFocus(obj, nextHandler):
    """Backward compatibility helper."""
    nextHandler()
    try:
        handleCalculatorFocus(obj)
    except Exception as e:
        log.error(f"win11_access: Error in calculator handleGainFocus: {e}")
