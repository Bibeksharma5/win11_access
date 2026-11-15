# Accessibility enhancement for Windows 11 (win11_access)

* Author: Bibek
* Version: 1.0
* Minimum NVDA Version: 2026.1
* Last Tested NVDA Version: 2026.3

This NVDA add-on provides targeted accessibility enhancements for Windows 11, improving the screen reading experience across core Windows experiences.

## Features

### 1. Windows Search (Start Menu) Context Menu Navigation
* **Issue Addressed**: When searching in the Windows 11 Start Menu and opening the context menu on a search result (e.g. via Application key or Shift+F10), navigating through items with the Up or Down arrow key caused NVDA to repeatedly announce "context menu list" before every item (e.g. *"context menu list, open 1 of 5"*, *"context menu list, open file location 2 of 5"*).
* **Enhancement**: The repetitive announcement of "context menu list" is suppressed while navigating menu items with Up or Down arrow keys. NVDA speaks only the relevant menu item and position (e.g. *"open 1 of 5"*, *"open file location 2 of 5"*), making browsing options faster and much easier to listen to. Context menus in other applications remain unaffected.

### 2. Windows Settings — Installed Apps Enhancements
* **Number of Apps Found Announcement**:
  * In Windows Settings under **Apps > Installed apps**, a text label displays the total count of applications (e.g. *"137 apps found"*).
  * When you navigate focus to the **Filter by drive** combo box, NVDA automatically announces the number of apps found.
* **Application Size in the App List**:
  * While navigating through the list of installed applications in Installed Apps, NVDA automatically announces each application's storage size (e.g. *"Google Chrome, 350 MB, list item, 1 of 137"*).
  * You no longer need to switch to NVDA object navigation to read the app size from the table column.

### 3. Windows Calculator Mode Announcement
* **Enhancement**: Upon opening the Windows 11 Calculator application, NVDA automatically announces the currently active calculation mode (e.g. *"Standard mode"*, *"Scientific mode"*, *"Programmer mode"*).

## Installation
1. Download or locate `win11_access.nvda-addon`.
2. Press `Enter` on the file or open it through the NVDA Add-ons Manager (`NVDA menu > Tools > Add-ons store / Add-ons Manager`).
3. Follow the prompts to install and restart NVDA.

## Requirements
* Windows 11 (latest releases)
* NVDA 2026.1 to 2026.3
