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
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_BASE = r"D:\Android\Temp" if os.path.isdir(r"D:\Android\Temp") else tempfile.gettempdir()
sys.path.insert(0, SCRIPT_DIR)
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

    # Test 7: Updater translation + in-app addon hook verification
    updater_code = files_data.get("dist/updater.js", b"").decode("utf-8")
    assert "Güncellemeleri Denetle" in updater_code, "'Güncellemeleri Denetle' missing from dist/updater.js"
    assert "Güncellemek için Yeniden Başlat" in updater_code, "'Güncellemek için Yeniden Başlat' missing from dist/updater.js"
    assert "ANTIGRAVITY_TR_UPDATER_HOOK_V1" in updater_code, "In-app updater addon hook missing from dist/updater.js"
    assert "update-downloaded" in updater_code and "quitAndInstall" in updater_code, "Updater hook missing update-downloaded/quitAndInstall lifecycle"
    print("[PASS] Test 7: dist/updater.js translations and in-app addon hook confirmed.")

    # Test 8: Backup existence verification
    ver = get_version(files_data)
    ext_bak = f"{DEFAULT_ASAR}.bak.{ver}"
    tool_bak = os.path.join(BACKUP_DIR, f"app.asar.bak.{ver}")
    orig_bak = f"{DEFAULT_ASAR}.bak.original"
    has_bak = os.path.exists(ext_bak) or os.path.exists(tool_bak) or os.path.exists(orig_bak) or (os.path.exists(BACKUP_DIR) and len(os.listdir(BACKUP_DIR)) > 0)
    assert has_bak, "Backup file not found!"
    print(f"[PASS] Test 8: Backup confirmed.")

    # Test 9: Dictionary JSON validity
    dict_path = os.path.join(SCRIPT_DIR, "tr-dictionary.json")
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

    # Test 11: Zero-background-daemon architecture & PowerShell 5.1 syntax checks
    import subprocess
    root_dir = SCRIPT_DIR
    post_update_ps = os.path.join(root_dir, "PostUpdate-AntigravityTR.ps1")
    shortcuts_ps = os.path.join(root_dir, "Configure-AntigravityShortcuts.ps1")
    launch_vbs = os.path.join(root_dir, "Launch-Antigravity.vbs")
    post_update_vbs = os.path.join(root_dir, "Start-AntigravityTR-PostUpdate.vbs")

    for req_file in [post_update_ps, shortcuts_ps, launch_vbs, post_update_vbs]:
        assert os.path.exists(req_file), f"Missing required addon file: {req_file}"

    assert not os.path.exists(os.path.join(root_dir, "Watch-AntigravityUpdate.ps1")), "Legacy background watcher Watch-AntigravityUpdate.ps1 must be removed"

    reg_check = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command",
         "if (Get-ItemProperty 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' -Name 'AntigravityTurkishAutoPatch' -ErrorAction SilentlyContinue) { exit 1 }"],
        capture_output=True, text=True
    )
    assert reg_check.returncode == 0, "Legacy HKCU Run key AntigravityTurkishAutoPatch still exists!"

    proc_check = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command",
         "$p = Get-CimInstance Win32_Process -Filter \"Name='powershell.exe'\" | Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -like '*-File*Watch-AntigravityUpdate.ps1*' -and $_.CommandLine -notmatch 'Get-CimInstance' }; if ($p) { exit 1 }"],
        capture_output=True, text=True
    )
    assert proc_check.returncode == 0, "Background Watch-AntigravityUpdate process is still running!"

    for ps_file in [post_update_ps, shortcuts_ps]:
        parse_cmd = [
            "powershell.exe", "-NoProfile", "-Command",
            f"$errs=$null; [void][System.Management.Automation.Language.Parser]::ParseFile('{ps_file}',[ref]$null,[ref]$errs); if($errs.Count -gt 0){{ $errs | Out-String; exit 1 }}"
        ]
        parse_res = subprocess.run(parse_cmd, capture_output=True, text=True)
        assert parse_res.returncode == 0, f"PowerShell syntax error in {ps_file}: {parse_res.stdout} {parse_res.stderr}"

    print("[PASS] Test 11: Zero-background-daemon state and PowerShell script syntax verified.")

    # Test 12: Ensure-AntigravityTR.ps1 parameter forwarding
    ensure_ps = os.path.join(SCRIPT_DIR, "Ensure-AntigravityTR.ps1")
    with open(ensure_ps, "r", encoding="utf-8") as f:
        ensure_code = f.read()
    assert "$Force" in ensure_code and "--force" in ensure_code, "--force forwarding missing in Ensure-AntigravityTR.ps1"
    print("[PASS] Test 12: Ensure-AntigravityTR.ps1 --force forwarding verified.")

    # Test 13: Behavioral test — one-shot PostUpdate guard re-patches updated ASAR and exits automatically
    import shutil, time
    test_root = os.path.join(TEMP_BASE, f"tr_postupdate_test_{os.getpid()}")
    os.makedirs(os.path.join(test_root, "antigravity", "resources"), exist_ok=True)
    try:
        mock_asar = os.path.join(test_root, "antigravity", "resources", "app.asar")
        with open(mock_asar, "w", encoding="utf-8") as f:
            f.write("PATCHED_OK_V1")

        mock_patcher = os.path.join(test_root, "mock_patcher.py")
        with open(mock_patcher, "w", encoding="utf-8") as f:
            f.write(
                "import sys, argparse\n"
                "p = argparse.ArgumentParser()\n"
                "p.add_argument('--asar', required=True)\n"
                "p.add_argument('--check', action='store_true')\n"
                "a = p.parse_args()\n"
                "with open(a.asar, 'r', encoding='utf-8') as f: c = f.read()\n"
                "if a.check:\n"
                "    sys.exit(0 if 'PATCHED_OK' in c else 1)\n"
                "with open(a.asar, 'w', encoding='utf-8') as f: f.write('PATCHED_OK_V2')\n"
            )

        mock_log = os.path.join(test_root, "postupdate.log")
        mock_stamp = os.path.join(test_root, ".last_patched_stamp")
        proc = subprocess.Popen(
            [
                "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", post_update_ps,
                "-AsarPath", mock_asar,
                "-PatcherScript", mock_patcher,
                "-StampPath", mock_stamp,
                "-LogPath", mock_log,
                "-MaxWaitSeconds", "12",
                "-DisableHotApply",
                "-SkipShortcuts",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        time.sleep(1.5)
        # Simulate NSIS update replacing app.asar inside recreated resources/
        res_dir = os.path.join(test_root, "antigravity", "resources")
        shutil.rmtree(res_dir)
        os.makedirs(res_dir, exist_ok=True)
        with open(mock_asar, "w", encoding="utf-8") as f:
            f.write("UNPATCHED_NEW_VERSION")

        out, err = proc.communicate(timeout=15)
        assert proc.returncode == 0, f"PostUpdate guard failed ({proc.returncode}): {out} {err}"
        with open(mock_asar, "r", encoding="utf-8") as f:
            content = f.read()
        assert "PATCHED_OK_V2" in content, f"PostUpdate did not re-patch updated ASAR! Content={content}"
        print("[PASS] Test 13: One-shot PostUpdate guard patched updated ASAR and exited cleanly.")
    finally:
        shutil.rmtree(test_root, ignore_errors=True)

    # Test 14: Shortcut wrapper install + restore preserves icon and restores original target
    lnk_root = os.path.join(TEMP_BASE, f"tr_lnk_test_{os.getpid()}")
    os.makedirs(lnk_root, exist_ok=True)
    try:
        mock_exe = r"C:\Windows\System32\notepad.exe"
        test_lnk = os.path.join(lnk_root, "Antigravity.lnk")
        backup_dir = os.path.join(lnk_root, "backup")
        create_cmd = (
            f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{test_lnk}');"
            f"$s.TargetPath='{mock_exe}'; $s.IconLocation='{mock_exe},0'; $s.Save()"
        )
        subprocess.run(["powershell.exe", "-NoProfile", "-Command", create_cmd], check=True)

        install_res = subprocess.run(
            [
                "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", shortcuts_ps,
                "-ShortcutPaths", test_lnk,
                "-TargetExe", mock_exe,
                "-BackupDir", backup_dir,
            ],
            capture_output=True, text=True, check=True
        )
        read_cmd = f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{test_lnk}'); \"$($s.TargetPath)|$($s.Arguments)|$($s.IconLocation)\""
        after_install = subprocess.run(["powershell.exe", "-NoProfile", "-Command", read_cmd], capture_output=True, text=True, check=True).stdout.strip()
        assert "wscript.exe" in after_install.lower() and "launch-antigravity.vbs" in after_install.lower(), f"Shortcut not wrapped: {after_install}"
        assert mock_exe.lower() in after_install.lower(), f"Original icon location not preserved: {after_install}"

        restore_res = subprocess.run(
            [
                "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", shortcuts_ps,
                "-Restore",
                "-ShortcutPaths", test_lnk,
                "-TargetExe", mock_exe,
                "-BackupDir", backup_dir,
            ],
            capture_output=True, text=True, check=True
        )
        after_restore = subprocess.run(["powershell.exe", "-NoProfile", "-Command", read_cmd], capture_output=True, text=True, check=True).stdout.strip()
        assert after_restore.lower().startswith(mock_exe.lower() + "|"), f"Shortcut not restored to original exe: {after_restore}"
        print("[PASS] Test 14: Shortcut wrapper install and clean restore verified.")
    finally:
        shutil.rmtree(lnk_root, ignore_errors=True)

    # Test 15: Sidebar/conversation translations present in tr-locale.js
    locale_path = os.path.join(SCRIPT_DIR, "tr-locale.js")
    with open(locale_path, "r", encoding="utf-8") as f:
        locale_src = f.read()
    for required_snippet in [
        '"Pinned Conversations": "Sabitlenen Sohbetler"',
        '"Archive Conversation": "Sohbeti Arşivle"',
        '"Unpin": "Sabitlemeyi Kaldır"',
        '/^Updated\\s+(.+)$/',
    ]:
        assert required_snippet in locale_src, f"Missing translation entry: {required_snippet}"
    print("[PASS] Test 15: Sidebar/conversation translations verified in tr-locale.js.")

    print("\n==========================================")
    print("ALL 15 TESTS PASSED SUCCESSFULLY (15/15).")
    print("==========================================")
    return True

if __name__ == "__main__":
    if not run_tests():
        sys.exit(1)