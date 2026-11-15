# -*- coding: UTF-8 -*-
# win11_access
# Accessibility enhancement for Windows 11 NVDA Add-on
# Author: Bibek

import globalPluginHandler
from logHandler import log

from . import search_context_menu
from . import installed_apps
from . import calculator


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    """
    Main Global Plugin for Windows 11 Accessibility Enhancements.
    Integrates enhancements for:
    - Windows Search (Start Menu) context menu item navigation
    - Windows Settings (Installed Apps) app count and application sizes
    - Windows Calculator active mode announcement on startup
    """

    def __init__(self):
        super().__init__()
        log.info("win11_access: Initializing Accessibility enhancement for Windows 11 add-on")
        try:
            search_context_menu.register()
        except Exception as e:
            log.error(f"win11_access: Failed to initialize search_context_menu: {e}")

    def terminate(self):
        log.info("win11_access: Terminating Accessibility enhancement for Windows 11 add-on")
        try:
            search_context_menu.unregister()
        except Exception as e:
            log.error(f"win11_access: Failed to unregister search_context_menu: {e}")
        super().terminate()

    def chooseNVDAObjectOverlayClasses(self, obj, clsList):
        """Applies overlay classes for Installed Apps list items."""
        try:
            installed_apps.chooseNVDAObjectOverlayClasses(obj, clsList)
        except Exception as e:
            log.error(f"win11_access: Error in chooseNVDAObjectOverlayClasses: {e}")

    def event_focusEntered(self, obj, nextHandler):
        """
        Suppresses repetitive 'context menu list' announcements when navigating
        Windows Search result context menu with Up/Down arrows.
        """
        try:
            search_context_menu.handleFocusEntered(obj, nextHandler)
        except Exception as e:
            log.error(f"win11_access: Error in event_focusEntered: {e}")
            nextHandler()

    def event_gainFocus(self, obj, nextHandler):
        """
        Handles focus gain events:
        - Speaks 'X apps found' when focusing drive filter combo box in Installed apps.
        - Speaks app size when navigating Installed apps list items.
        - Triggers active mode announcement when opening Calculator.
        """
        try:
            installed_apps.handleGainFocus(obj, nextHandler)
        except Exception as e:
            log.error(f"win11_access: Error in installed_apps.handleGainFocus: {e}")
            nextHandler()

        try:
            calculator.handleGainFocus(obj, lambda: None)
        except Exception as e:
            log.error(f"win11_access: Error in calculator.handleGainFocus: {e}")

    def event_foreground(self, obj, nextHandler):
        """Handles foreground window change to detect when Calculator opens."""
        try:
            calculator.handleForeground(obj, nextHandler)
        except Exception as e:
            log.error(f"win11_access: Error in calculator.handleForeground: {e}")
            nextHandler()
