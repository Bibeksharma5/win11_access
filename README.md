# Accessibility enhancement for Windows 11 (win11_access)

**win11_access** is an NVDA add-on created to enhance accessibility across Windows 11 by addressing specific usability friction points and improving navigation in core system interfaces.

## Add-on Information

* **Package Name:** `win11_access.nvda-addon`
* **Internal Name:** `win11_access`
* **Summary:** `Accessibility enhancement for windows 11`
* **Version:** `1.0`
* **Author:** `Bibek`
* **Minimum NVDA Version:** `2026.1`
* **Last Tested NVDA Version:** `2026.3`
* **Target OS:** Windows 11 (latest releases)

---

## Enhancements Included in Version 1.0

### 1. Windows Search (Start Menu) — Context Menu Arrow Navigation
* **Problem in Windows 11:** When searching in the Windows 11 Start Menu and opening the context menu on a search result (via Application key or `Shift + F10`), navigating between options using the `Up` or `Down` arrow keys caused NVDA to redundantly announce `"context menu list"` on every single item (e.g. *"context menu list, open 1 of 5"*, *"context menu list, open file location 2 of 5"*, *"context menu list, run as administrator 3 of 5"*).
* **Enhancement:** Suppresses the repetitive announcement of `"context menu list"` when navigating with `Up` and `Down` arrow keys. NVDA speaks only the relevant action item and position (e.g. *"open file location 2 of 5"*). Context menus in other applications (such as File Explorer or desktop) are completely unaffected.

### 2. Windows Settings — Installed Apps Page Enhancements
* **2a. Total Number of Apps Announcement:**
  * In Windows 11 Settings under **Apps > Installed apps**, the total number of installed applications is displayed (e.g. *"137 apps found"*).
  * When focus lands on the **Filter by drive** combo box, NVDA automatically speaks the apps count text.
* **2b. Application Size Announcement in the App List:**
  * While navigating through the list of installed applications, NVDA now speaks each application's storage size (e.g. *"Google Chrome, 350 MB, list item, 1 of 137"*).
  * Users no longer have to use NVDA object navigation to locate and read the size column.

### 3. Windows Calculator — Calculation Mode Announcement
* **Enhancement:** Upon opening the Windows 11 Calculator application, NVDA automatically detects and announces the currently active calculation mode (e.g. *"Standard mode"*, *"Scientific mode"*, *"Programmer mode"*).

---

## Directory Structure

```text
d:\win11 accessibility\
├── addon\
│   ├── manifest.ini
│   ├── doc\
│   │   └── en\
│   │       ├── readme.html
│   │       └── readme.md
│   └── globalPlugins\
│       └── win11_access\
│           ├── __init__.py               # Main GlobalPlugin coordinator
│           ├── search_context_menu.py    # Search result context menu enhancement
│           ├── installed_apps.py         # Installed apps count and size enhancements
│           └── calculator.py             # Calculator active mode announcement
├── tests\
│   ├── nvda_mocks.py                    # Lightweight NVDA environment mocks for testing
│   ├── test_manifest.py                 # Manifest syntax and metadata tests
│   ├── test_search_context_menu.py      # Search context menu unit tests
│   ├── test_installed_apps.py           # Installed apps unit tests
│   └── test_calculator.py               # Calculator mode detection unit tests
├── build.py                             # Build and packaging script
├── win11_access.nvda-addon              # Compiled NVDA add-on package
└── README.md                            # Documentation
```

---

## Testing & Building

### Running Unit Tests
All unit tests can be executed with standard Python:
```powershell
python -m unittest discover tests
```

### Compiling the Package
To build and package the `.nvda-addon` file:
```powershell
python build.py
```
This validates the manifest, compiles the Python sources to verify syntax, packages the clean ZIP bundle, and outputs `win11_access.nvda-addon`.

---

## Installation in NVDA
1. Ensure NVDA (version 2026.1 or later) is running.
2. Open or press `Enter` on `win11_access.nvda-addon` in File Explorer.
3. When NVDA asks for installation confirmation, select **Yes**.
4. Restart NVDA when prompted.
