# -*- coding: UTF-8 -*-
# nvda_mocks.py
# Provides lightweight mocks for NVDA modules so unit tests can run independently.

import sys
from types import ModuleType

# Setup controlTypes mock
controlTypes = ModuleType("controlTypes")
class Role:
    UNKNOWN = 0
    WINDOW = 1
    MENUBAR = 2
    POPUPMENU = 3
    MENU = 4
    MENUITEM = 5
    LIST = 6
    LISTITEM = 7
    COMBOBOX = 8
    TABLE = 9
    TABLEROW = 10
    DATAITEM = 11
    DATAGRID = 12
    STATICTEXT = 13
    LABEL = 14
    TABLEBODY = 15
controlTypes.Role = Role

# Setup winUser mock
winUser = ModuleType("winUser")
winUser.VK_UP = 38
winUser.VK_DOWN = 40
winUser.GA_ROOT = 2
winUser._key_states = {}
winUser._window_texts = {}
def getKeyState(vk):
    return winUser._key_states.get(vk, 0)
def getAncestor(hwnd, ga):
    return hwnd
def isWindow(hwnd):
    return True
def getWindowText(hwnd):
    return winUser._window_texts.get(hwnd, "")
winUser.getKeyState = getKeyState
winUser.getAncestor = getAncestor
winUser.isWindow = isWindow
winUser.getWindowText = getWindowText

# Setup keyboardHandler mock
keyboardHandler = ModuleType("keyboardHandler")
keyboardHandler.lastPassThroughKeyDown = None

# Setup inputCore mock
inputCore = ModuleType("inputCore")
class _Decider:
    def __init__(self):
        self.callbacks = []
    def register(self, fn):
        self.callbacks.append(fn)
    def unregister(self, fn):
        if fn in self.callbacks:
            self.callbacks.remove(fn)
    def decide(self, *args, **kwargs):
        for cb in self.callbacks:
            if not cb(*args, **kwargs):
                return False
        return True
inputCore.decide_executeGesture = _Decider()

# Setup logHandler mock
logHandler = ModuleType("logHandler")
class _Log:
    def debug(self, msg): pass
    def info(self, msg): pass
    def error(self, msg): pass
logHandler.log = _Log()

# Setup NVDAObjects.UIA mock
nvdaObjects = ModuleType("NVDAObjects")
nvdaObjectsUIA = ModuleType("NVDAObjects.UIA")
class BaseUIA:
    def __init__(self, name="", role=0, UIAAutomationId="", children=None, parent=None, previous=None, next=None):
        self._name = name
        self._description = ""
        self.role = role
        self.UIAAutomationId = UIAAutomationId
        self.children = children or []
        self.parent = parent
        self.previous = previous
        self.next = next
        self.windowHandle = 1001
        self.appModule = None

    def _get_name(self):
        return self._name

    @property
    def name(self):
        return self._get_name()

    @name.setter
    def name(self, val):
        self._name = val

    def _get_description(self):
        return self._description

    @property
    def description(self):
        return self._get_description()

    @description.setter
    def description(self, val):
        self._description = val

    def event_focusEntered(self):
        pass

    def event_gainFocus(self):
        pass

nvdaObjectsUIA.UIA = BaseUIA
nvdaObjects.UIA = nvdaObjectsUIA

# Setup api mock
api = ModuleType("api")
api._foreground = None
api._focus = None
def getForegroundObject():
    return api._foreground
def getFocusObject():
    return api._focus
api.getForegroundObject = getForegroundObject
api.getFocusObject = getFocusObject

# Setup core mock
core = ModuleType("core")
def callLater(delay, func, *args, **kwargs):
    return func(*args, **kwargs)
core.callLater = callLater

# Setup ui mock
ui = ModuleType("ui")
ui.messages = []
def message(msg):
    ui.messages.append(msg)
ui.message = message

# Setup globalPluginHandler mock
globalPluginHandler = ModuleType("globalPluginHandler")
class GlobalPlugin:
    def __init__(self): pass
    def terminate(self): pass
globalPluginHandler.GlobalPlugin = GlobalPlugin

# Setup appModuleHandler mock
appModuleHandler = ModuleType("appModuleHandler")
class AppModule:
    def __init__(self, processID=0, appName=""):
        self.processID = processID
        self.appName = appName
    def chooseNVDAObjectOverlayClasses(self, obj, clsList): pass
    def event_gainFocus(self, obj, nextHandler): nextHandler()
    def event_foreground(self, obj, nextHandler): nextHandler()
appModuleHandler.AppModule = AppModule
appModuleHandler._registeredExecutables = {}
def registerExecutableWithAppModule(executableName, appModName):
    appModuleHandler._registeredExecutables[executableName] = appModName
def unregisterExecutable(executableName):
    appModuleHandler._registeredExecutables.pop(executableName, None)
appModuleHandler.registerExecutableWithAppModule = registerExecutableWithAppModule
appModuleHandler.unregisterExecutable = unregisterExecutable

# Setup nvdaBuiltin mock
nvdaBuiltin = ModuleType("nvdaBuiltin")
nvdaBuiltinAppModules = ModuleType("nvdaBuiltin.appModules")
nvdaBuiltin.appModules = nvdaBuiltinAppModules

def install_mocks():
    sys.modules["controlTypes"] = controlTypes
    sys.modules["winUser"] = winUser
    sys.modules["keyboardHandler"] = keyboardHandler
    sys.modules["inputCore"] = inputCore
    sys.modules["logHandler"] = logHandler
    sys.modules["NVDAObjects"] = nvdaObjects
    sys.modules["NVDAObjects.UIA"] = nvdaObjectsUIA
    sys.modules["api"] = api
    sys.modules["core"] = core
    sys.modules["ui"] = ui
    sys.modules["globalPluginHandler"] = globalPluginHandler
    sys.modules["appModuleHandler"] = appModuleHandler
    sys.modules["nvdaBuiltin"] = nvdaBuiltin
    sys.modules["nvdaBuiltin.appModules"] = nvdaBuiltinAppModules
