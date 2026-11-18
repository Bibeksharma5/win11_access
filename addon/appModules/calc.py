# -*- coding: UTF-8 -*-
# calc.py
# NVDA App Module for Windows Calculator (calc.exe)
# Part of win11_access add-on.
# Author: Bibek Sharma Dhakal

try:
    from .calculator import AppModule
except ImportError:
    from appModules.calculator import AppModule
