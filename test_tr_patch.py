#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Verification suite for Antigravity Turkish Language Patch
Path: D:\Android\Tools\Antigravity-TR\test_tr_patch.py
"""

import sys
import os
import json
import re

sys.path.insert(0, r"D:\Android\Tools\Antigravity-TR")
from patch_asar import read_asar, is_patched, get_version, DEFAULT_ASAR, BACKUP_DIR, LOCALE_SCRIPT_PATH

def run_tests():
    print("=== Antigravity Turkish Patch Comprehensive Verification Suite ===")

    # Test 1: Check ASAR existence
    assert os.path.exists(DEFAULT_ASAR), f"ASAR does not exist: {DEFAULT_ASAR}"
    print("[PASS] Test 1: app.asar exists on disk.")

    # Test 2: Parse ASAR structure
    header, files_data = read_asar(DEFAULT_ASAR)
    assert len(files_data) > 500, f"Expected >500 files, got {len(files_data)}"
    print(f"[PASS] Test 2: ASAR parsed successfully ({len(files_data)} files).")

    # Test 3: Check Patch signature
    assert is_patched(files_data), "Patch signature ANTIGRAVITY_TR_PATCH_V1 not found in preload.js"
    print("[PASS] Test 3: Patch signature ANTIGRAVITY_TR_PATCH_V1 confirmed.")

    # Test 4: Menu translation verification
    menu_code = files_data.get("dist/menu.js", b"").decode("utf-8")
    assert "Yeni Pencere" in menu_code, "'Yeni Pencere' missing from dist/menu.js"
    assert "Belgeler" in menu_code, "'Belgeler' missing from dist/menu.js"
    assert "WSL\\'ye Bağlan" in menu_code or "WSL'ye Bağlan" in menu_code, "'WSL\\'ye Bağlan' missing from dist/menu.js"
    print("[PASS] Test 4: dist/menu.js translations confirmed.")

    # Test 5: Tray translation verification
    tray_code = files_data.get("dist/tray.js", b"").decode("utf-8")
    assert "Çalışan ajan yok" in tray_code, "'Çalışan ajan yok' missing from dist/tray.js"
    print("[PASS] Test 5: dist/tray.js translations confirmed.")

    # Test 6: Main dialog translation verification
    main_code = files_data.get("dist/main.js", b"").decode("utf-8")
    assert "Çıkışı Onayla" in main_code, "'Çıkışı Onayla' missing from dist/main.js"
    assert "Çıkmak istediğinizden emin misiniz?" in main_code, "Quit prompt missing from dist/main.js"
    print("[PASS] Test 6: dist/main.js translations confirmed.")

    # Test 7: Updater translation verification
    updater_code = files_data.get("dist/updater.js", b"").decode("utf-8")
    assert "Güncellemeleri Denetle" in updater_code, "'Güncellemeleri Denetle' missing from dist/updater.js"
    assert "Güncellemek için Yeniden Başlat" in updater_code, "'Güncellemek için Yeniden Başlat' missing from dist/updater.js"
    print("[PASS] Test 7: dist/updater.js translations confirmed.")

    # Test 8: Backup existence verification
    ver = get_version(files_data)
    ext_bak = f"{DEFAULT_ASAR}.bak.{ver}"
    tool_bak = os.path.join(BACKUP_DIR, f"app.asar.bak.{ver}")
    orig_bak = f"{DEFAULT_ASAR}.bak.original"
    has_bak = os.path.exists(ext_bak) or os.path.exists(tool_bak) or os.path.exists(orig_bak) or (os.path.exists(BACKUP_DIR) and len(os.listdir(BACKUP_DIR)) > 0)
    assert has_bak, "Backup file not found!"
    print(f"[PASS] Test 8: Backup confirmed.")

    # Test 9: Dictionary JSON validity
    dict_path = r"D:\Android\Tools\Antigravity-TR\tr-dictionary.json"
    assert os.path.exists(dict_path), "tr-dictionary.json missing"
    with open(dict_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert "exact" in data and len(data["exact"]) >= 150, "Dictionary incomplete"
        assert "patterns" in data and len(data["patterns"]) >= 10, "Patterns incomplete"
    print(f"[PASS] Test 9: tr-dictionary.json valid ({len(data['exact'])} terms, {len(data['patterns'])} patterns).")

    # Test 10: tr-locale.js attribute observation & re-entry guard
    with open(LOCALE_SCRIPT_PATH, "r", encoding="utf-8") as f:
        loc = f.read()
    assert "attributes: true" in loc, "attributes: true missing from tr-locale.js"
    assert "attributeFilter:" in loc, "attributeFilter missing from tr-locale.js"
    assert "__ANTIGRAVITY_TR_OBSERVER__" in loc, "Observer lifecycle handle missing"
    assert "isMutating" in loc, "isMutating loop guard missing"
    print("[PASS] Test 10: tr-locale.js attribute observation and loop guard verified.")

    # Test 11: Watch-AntigravityUpdate.ps1 MessageData verification (no broken $using:)
    watcher_ps = r"D:\Android\Tools\Antigravity-TR\Watch-AntigravityUpdate.ps1"
    with open(watcher_ps, "r", encoding="utf-8") as f:
        watch_code = f.read()
    assert "$using:" not in watch_code, "Broken $using: found in Watch-AntigravityUpdate.ps1"
    assert "MessageData" in watch_code, "MessageData missing in Watch-AntigravityUpdate.ps1"
    print("[PASS] Test 11: Watch-AntigravityUpdate.ps1 PowerShell 5.1 compatibility verified.")

    # Test 12: Ensure-AntigravityTR.ps1 parameter forwarding
    ensure_ps = r"D:\Android\Tools\Antigravity-TR\Ensure-AntigravityTR.ps1"
    with open(ensure_ps, "r", encoding="utf-8") as f:
        ensure_code = f.read()
    assert "$Force" in ensure_code and "--force" in ensure_code, "--force forwarding missing in Ensure-AntigravityTR.ps1"
    print("[PASS] Test 12: Ensure-AntigravityTR.ps1 --force forwarding verified.")

    print("\n==========================================")
    print("ALL 12 TESTS PASSED SUCCESSFULLY (12/12).")
    print("==========================================")
    return True

if __name__ == "__main__":
    if not run_tests():
        sys.exit(1)