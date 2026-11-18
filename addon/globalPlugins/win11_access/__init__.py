# -*- coding: UTF-8 -*-
# win11_access
# Accessibility enhancement for Windows 11 NVDA Add-on
# Author: Bibek Sharma Dhakal

import globalPluginHandler
from logHandler import log

from . import search_context_menu

try:
    import appModuleHandler
except ImportError:
    appModuleHandler = None


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    """
    Main Global Plugin for Windows 11 Accessibility Enhancements.
    Integrates enhancements for:
    - Windows Search (Start Menu) context menu item navigation

    Note:
    Enhancements for Windows Settings (Installed Apps) and Windows Calculator
    are implemented in application-specific App Modules (appModules/systemsettings.py,
    appModules/calculatorapp.py, appModules/calculator.py) so they operate effortlessly
    per application rather than consuming global focus events.
    """

    def __init__(self):
        super().__init__()
        log.info("win11_access: Initializing Accessibility enhancement for Windows 11 add-on")
        try:
            search_context_menu.register()
        except Exception as e:
            log.error(f"win11_access: Failed to initialize search_context_menu: {e}")

        # Register executable aliases if appModuleHandler supports it
        if appModuleHandler and hasattr(appModuleHandler, "registerExecutableWithAppModule"):
            try:
                appModuleHandler.registerExecutableWithAppModule("calculatorapp", "calculator")
                appModuleHandler.registerExecutableWithAppModule("calc", "calculator")
            except Exception as e:
                log.debug(f"win11_access: registerExecutableWithAppModule note: {e}")

    def terminate(self):
        log.info("win11_access: Terminating Accessibility enhancement for Windows 11 add-on")
        try:
            search_context_menu.unregister()
        except Exception as e:
            log.error(f"win11_access: Failed to unregister search_context_menu: {e}")

        if appModuleHandler and hasattr(appModuleHandler, "unregisterExecutable"):
            try:
                appModuleHandler.unregisterExecutable("calculatorapp")
                appModuleHandler.unregisterExecutable("calc")
            except Exception as e:
                log.debug(f"win11_access: unregisterExecutable note: {e}")

        super().terminate()

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
