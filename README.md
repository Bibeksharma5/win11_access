# Accessibility Enhancement for Windows 11 (`win11_access`)

An NVDA add-on providing lightweight but important accessibility enhancements for Windows 11, inspired by [Windows App Essentials](https://github.com/josephsl/wintenApps).

---

## Add-on Information

* **Version:** 1.0
* **Author:** Bibek Sharma Dhakal
* **Homepage:** [https://github.com/Bibeksharma5/win11_access](https://github.com/Bibeksharma5/win11_access)
* **NVDA Compatibility:** 2026.1 to 2026.3
* **Target OS:** Windows 11

---

## Features

* **Windows Search (Start Menu):** Suppresses the repetitive `"context menu list"` announcement when navigating search result context menu options with the Up and Down arrow keys.
* **Windows Settings (Installed Apps):**
  * **App Count Announcement:** Automatically speaks the total number of apps found when focusing the "Filter by drive" combo box.
  * **Application Size:** Speaks each application's storage size (e.g. *"Google Chrome, 350 MB"*) while navigating through the installed applications list without requiring object navigation.
* **Windows Calculator:** Automatically announces the active calculation mode (e.g. Standard, Scientific, Programmer) upon opening the application.

---

## Installation

1. Download `win11_access.nvda-addon` from the [releases page](https://github.com/Bibeksharma5/win11_access/releases).
2. Press `Enter` on the file or install it via NVDA Menu > **Tools** > **Add-on Store**.
3. Select **Yes** to confirm installation and restart NVDA.

---

## Development & Testing

* **Run tests:**
  ```powershell
  python -m unittest discover tests
  ```
* **Build package:**
  ```powershell
  python build.py
  ```

---

## Notes

* This add-on was developed independently from scratch without utilizing or borrowing any external source code.
* This add-on has been tested with the latest Windows 11 builds.
* If you would like to see any new feature or enhancement integrated, you are welcome to report suggestions or open an issue on the [GitHub Issue Tracker](https://github.com/Bibeksharma5/win11_access/issues).
