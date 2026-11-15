#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# build.py
# Compiles and packages the NVDA add-on into win11_access.nvda-addon.

import os
import sys
import zipfile
import py_compile
import re

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ADDON_DIR = os.path.join(ROOT_DIR, "addon")
OUTPUT_PACKAGE = os.path.join(ROOT_DIR, "win11_access.nvda-addon")


def validate_manifest():
    manifest_path = os.path.join(ADDON_DIR, "manifest.ini")
    if not os.path.isfile(manifest_path):
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        content = f.read()

    def get_val(key):
        m = re.search(rf'^{key}\s*=\s*(.+)$', content, re.MULTILINE)
        if not m:
            return None
        val = m.group(1).strip()
        if val.startswith('"""'):
            m2 = re.search(rf'^{key}\s*=\s*"""(.*?)"""', content, re.DOTALL | re.MULTILINE)
            return m2.group(1).strip() if m2 else val
        return val.strip('"\'')

    name = get_val("name")
    summary = get_val("summary")
    version = get_val("version")
    min_version = get_val("minimumNVDAVersion")
    last_version = get_val("lastTestedNVDAVersion")

    print(f"Manifest Validation:")
    print(f"  Name: {name}")
    print(f"  Summary: {summary}")
    print(f"  Version: {version}")
    print(f"  Minimum NVDA Version: {min_version}")
    print(f"  Last Tested NVDA Version: {last_version}")

    assert name == "win11_access", f"Expected name 'win11_access', got '{name}'"
    assert version == "1.0", f"Expected version '1.0', got '{version}'"
    assert min_version == "2026.1", f"Expected minimumNVDAVersion '2026.1', got '{min_version}'"
    assert last_version == "2026.3", f"Expected lastTestedNVDAVersion '2026.3', got '{last_version}'"
    print("  [OK] Manifest validated successfully.")


def compile_python_sources():
    print("Compiling Python sources to check syntax...")
    count = 0
    for root, _, files in os.walk(ADDON_DIR):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                py_compile.compile(path, doraise=True)
                count += 1
                rel = os.path.relpath(path, ADDON_DIR)
                print(f"  [OK] Compiled: {rel}")
    print(f"Successfully checked {count} Python source files.")


def package_addon():
    print(f"Creating add-on package: {OUTPUT_PACKAGE}")
    if os.path.exists(OUTPUT_PACKAGE):
        os.remove(OUTPUT_PACKAGE)

    with zipfile.ZipFile(OUTPUT_PACKAGE, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(ADDON_DIR):
            # Exclude __pycache__ and temporary files
            dirs[:] = [d for d in dirs if d != "__pycache__" and not d.startswith(".")]
            for file in files:
                if file.endswith((".pyc", ".pyo", ".tmp")) or file.startswith("."):
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, ADDON_DIR)
                z.write(file_path, arcname)
                print(f"  Added: {arcname}")

    pkg_size = os.path.getsize(OUTPUT_PACKAGE)
    print(f"Package created successfully! Size: {pkg_size} bytes ({pkg_size / 1024:.1f} KB)")


def verify_package():
    print("Verifying package contents...")
    with zipfile.ZipFile(OUTPUT_PACKAGE, "r") as z:
        names = z.namelist()
        assert "manifest.ini" in names, "manifest.ini missing from root of archive!"
        assert "globalPlugins/win11_access/__init__.py" in names, "Main global plugin missing!"
        assert "globalPlugins/win11_access/search_context_menu.py" in names, "Search context menu module missing!"
        assert "globalPlugins/win11_access/installed_apps.py" in names, "Installed apps module missing!"
        assert "globalPlugins/win11_access/calculator.py" in names, "Calculator module missing!"
        assert any(n.startswith("doc/") for n in names), "Documentation missing!"
    print("  [OK] Package verification passed! All required components are present.")


def main():
    validate_manifest()
    compile_python_sources()
    package_addon()
    verify_package()
    print("\nBUILD SUCCESSFUL! Ready for installation in NVDA.")


if __name__ == "__main__":
    main()
