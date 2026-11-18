# -*- coding: UTF-8 -*-
# calculatorapp.py
# NVDA App Module for Windows 11 Calculator (CalculatorApp.exe)
# Part of win11_access add-on.
# Author: Bibek Sharma Dhakal

try:
    from .calculator import AppModule
except ImportError:
    from appModules.calculator import AppModule
