# -*- coding: UTF-8 -*-
# calculator.py
# Enhancement for Windows 11 Calculator:
# Announces the currently active calculation mode (e.g. Standard mode, Scientific mode,
# Programmer mode) upon opening the Calculator application.

import api
import core
import ui
import winUser
from logHandler import log
import NVDAObjects.UIA

# Set of calculator window handles (HWNDs) that have already had their mode announced
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
        if isinstance(curr, getattr(NVDAObjects.UIA, "UIA", tuple())):
            try:
                currAutoId = (getattr(curr, "UIAAutomationId", "") or "").lower()
            except Exception:
                currAutoId = ""
        else:
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
                currNameLower = currName.lower()
                for mode in KNOWN_CALCULATOR_MODES:
                    modeLower = mode.lower()
                    if currNameLower == modeLower or currNameLower == f"{modeLower} calculator":
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


def getCalculatorMode():
    """
    Attempts to identify the currently active calculation mode in Calculator.
    Checks candidate objects (focusObject, foregroundObject), window titles,
    and descendant elements.
    Returns mode name string if found, otherwise None.
    """
    candidates = []

    focusObj = api.getFocusObject()
    if focusObj and isCalculatorApp(focusObj):
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

    # Step 1: Check window title for formatted mode (e.g. "Standard - Calculator")
    for root in candidates:
        hwnd = getattr(root, "windowHandle", None)
        if hwnd:
            try:
                title = winUser.getWindowText(hwnd) or ""
                if " - calculator" in title.lower():
                    modePart = title.split(" - ")[0].strip()
                    for mode in KNOWN_CALCULATOR_MODES:
                        if mode.lower() == modePart.lower():
                            return mode
            except Exception:
                pass

    # Step 2: Search for Header element or known modes from each candidate and its root
    for root in candidates:
        # Walk up to find the top container
        top = root
        curr = root
        for _ in range(6):
            p = getattr(curr, "parent", None)
            if not p:
                break
            top = p
            curr = p

        # Check AutomationId "Header" or "HeaderTitleText"
        for searchRoot in (top, root):
            for headerId in ("Header", "HeaderTitleText", "NormalHeader"):
                header = _findElementByAutoId(searchRoot, headerId, maxDepth=8)
                if header:
                    name = getattr(header, "name", "") or ""
                    if name and name.strip():
                        return name.strip()

        # Check known mode names in descendants
        for searchRoot in (top, root):
            mode = _findKnownModeInDescendants(searchRoot, maxDepth=8)
            if mode:
                return mode

    return None


def _announceModeCallback(rootHwnd, retryCount=0):
    """Callback function scheduled to run after Calculator opens to announce the mode."""
    mode = getCalculatorMode()
    if mode:
        if "mode" in mode.lower() or "calculator" in mode.lower():
            message = mode
        else:
            message = f"{mode} mode"
        ui.message(message)
        log.info(f"win11_access: Announced Calculator mode: {message}")
    elif retryCount < 4:
        # If UI elements haven't fully rendered in the WinUI 3 XAML island, retry after 150ms
        core.callLater(150, lambda: _announceModeCallback(rootHwnd, retryCount + 1))


def handleCalculatorFocus(obj):
    """
    Called on focus or foreground events.
    Detects if this is a newly opened Calculator window and schedules mode announcement.
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
        _announcedCalculatorHwnds.add(rootHwnd)
        # Clean up stale window handles
        try:
            _announcedCalculatorHwnds = {h for h in _announcedCalculatorHwnds if winUser.isWindow(h)}
        except Exception:
            pass

        # Schedule mode announcement after 200ms to allow UI elements to render
        core.callLater(200, lambda: _announceModeCallback(rootHwnd, 0))


def handleForeground(obj, nextHandler):
    """Called from GlobalPlugin.event_foreground."""
    nextHandler()
    try:
        handleCalculatorFocus(obj)
    except Exception as e:
        log.error(f"win11_access: Error in calculator handleForeground: {e}")


def handleGainFocus(obj, nextHandler):
    """Called from GlobalPlugin.event_gainFocus."""
    nextHandler()
    try:
        handleCalculatorFocus(obj)
    except Exception as e:
        log.error(f"win11_access: Error in calculator handleGainFocus: {e}")
