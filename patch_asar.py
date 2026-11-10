#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Antigravity Turkish Language Patcher
Path: D:\Android\Tools\Antigravity-TR\patch_asar.py
"""

import sys
import os
import struct
import json
import shutil
import argparse
import subprocess
import hashlib

PATCH_SIGNATURE = "/* ANTIGRAVITY_TR_PATCH_V1 */"
UPDATER_HOOK_SIGNATURE = "/* ANTIGRAVITY_TR_UPDATER_HOOK_V1 */"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ASAR = os.path.expandvars(r"%LOCALAPPDATA%\Programs\antigravity\resources\app.asar")
BACKUP_DIR = os.path.join(SCRIPT_DIR, "backups")
LOCALE_SCRIPT_PATH = os.path.join(SCRIPT_DIR, "tr-locale.js")
TEMP_DIR = r"D:\Android\Temp" if os.path.isdir(r"D:\Android\Temp") else os.environ.get("TEMP", "/tmp")
STAMP_FILE_PATH = os.path.join(SCRIPT_DIR, ".last_patched_stamp")


def read_asar(asar_path):
    with open(asar_path, "rb") as f:
        v1, v2, v3, v4 = struct.unpack("<IIII", f.read(16))
        header_json_bytes = f.read(v4)
        header = json.loads(header_json_bytes.decode("utf-8"))
        data_start = 8 + v2

        files_data = {}

        def extract(node, prefix=""):
            for k, v in node.get("files", {}).items():
                p = f"{prefix}/{k}" if prefix else k
                if "files" in v:
                    extract(v, p)
                elif not v.get("unpacked", False):
                    offset = int(v["offset"])
                    size = int(v["size"])
                    f.seek(data_start + offset)
                    files_data[p] = f.read(size)
                    if len(files_data[p]) != size:
                        raise ValueError(f"Corrupt ASAR: {p} expected {size} bytes, got {len(files_data[p])}")

        extract(header)
    return header, files_data


def calculate_integrity(data, block_size=4194304):
    blocks = []
    for i in range(0, len(data), block_size):
        chunk = data[i:i + block_size]
        blocks.append(hashlib.sha256(chunk).hexdigest())
    full_hash = hashlib.sha256(data).hexdigest()
    return {
        "algorithm": "SHA256",
        "hash": full_hash,
        "blockSize": block_size,
        "blocks": blocks,
    }


def write_asar(out_path, header, files_data):
    # Recalculate offsets, sizes, and integrity hashes
    cur_offset = 0

    def update_header(node, prefix=""):
        nonlocal cur_offset
        for k, v in node.get("files", {}).items():
            p = f"{prefix}/{k}" if prefix else k
            if "files" in v:
                update_header(v, p)
            elif not v.get("unpacked", False):
                content = files_data[p]
                v["size"] = len(content)
                v["offset"] = str(cur_offset)
                cur_offset += len(content)
                if "integrity" in v:
                    v["integrity"] = calculate_integrity(content)

    update_header(header)

    header_json = json.dumps(header, separators=(",", ":")).encode("utf-8")
    header_str_len = len(header_json)
    pad = (4 - (header_str_len % 4)) % 4
    header_padding = b"\0" * pad
    header_obj_size = header_str_len + pad + 4
    header_size = header_str_len + pad + 8
    magic = 4

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(struct.pack("<IIII", magic, header_size, header_obj_size, header_str_len))
        f.write(header_json)
        if pad > 0:
            f.write(header_padding)

        # Write files in the exact order of offsets
        def write_files(node, prefix=""):
            for k, v in node.get("files", {}).items():
                p = f"{prefix}/{k}" if prefix else k
                if "files" in v:
                    write_files(v, p)
                elif not v.get("unpacked", False):
                    f.write(files_data[p])

        write_files(header)


def is_patched(files_data):
    preload = files_data.get("dist/preload.js", b"").decode("utf-8", errors="replace")
    if PATCH_SIGNATURE not in preload:
        return False
    if "dist/updater.js" in files_data:
        updater = files_data["dist/updater.js"].decode("utf-8", errors="replace")
        if UPDATER_HOOK_SIGNATURE not in updater:
            return False
    return True


def build_updater_hook():
    vbs_js = json.dumps(os.path.join(SCRIPT_DIR, "Start-AntigravityTR-PostUpdate.vbs"))
    ps_js = json.dumps(os.path.join(SCRIPT_DIR, "PostUpdate-AntigravityTR.ps1"))
    return f"""
{UPDATER_HOOK_SIGNATURE}
;(function () {{
  try {{
    if (process.platform !== 'win32') return;
    const fsMod = require('fs');
    const cp = require('child_process');
    const updater = require('electron-updater').autoUpdater;
    const {{ app }} = require('electron');
    let pendingUpdate = false;
    let guardSpawned = false;

    function spawnPostUpdateGuard() {{
      if (guardSpawned || !pendingUpdate) return;
      guardSpawned = true;
      try {{
        const vbsScript = {vbs_js};
        const psScript = {ps_js};
        if (fsMod.existsSync(vbsScript)) {{
          const child = cp.spawn('wscript.exe', [vbsScript, String(process.pid)], {{
            detached: true,
            stdio: 'ignore',
            windowsHide: true,
          }});
          child.unref();
        }} else if (fsMod.existsSync(psScript)) {{
          const child = cp.spawn('powershell.exe', [
            '-WindowStyle', 'Hidden', '-NoProfile', '-ExecutionPolicy', 'Bypass',
            '-File', psScript, '-OldPid', String(process.pid)
          ], {{
            detached: true,
            stdio: 'ignore',
            windowsHide: true,
          }});
          child.unref();
        }}
      }} catch (e) {{
        console.error('[Antigravity-TR] Failed to spawn post-update guard:', e);
      }}
    }}

    if (updater && typeof updater.on === 'function') {{
      updater.on('update-downloaded', () => {{
        pendingUpdate = true;
      }});
      if (typeof updater.quitAndInstall === 'function') {{
        const origQuitAndInstall = updater.quitAndInstall.bind(updater);
        updater.quitAndInstall = function (...args) {{
          pendingUpdate = true;
          spawnPostUpdateGuard();
          return origQuitAndInstall(...args);
        }};
      }}
    }}
    if (app && typeof app.on === 'function') {{
      app.on('will-quit', () => {{
        if (pendingUpdate) spawnPostUpdateGuard();
      }});
      app.on('quit', () => {{
        if (pendingUpdate) spawnPostUpdateGuard();
      }});
    }}
  }} catch (e) {{
    console.error('[Antigravity-TR] Updater hook init failed:', e);
  }}
}})();
"""


def get_version(files_data):
    pkg_bytes = files_data.get("package.json", b"")
    if pkg_bytes:
        try:
            return json.loads(pkg_bytes.decode("utf-8")).get("version", "unknown")
        except Exception:
            pass
    return "unknown"


def has_any_patch(files_data):
    preload = files_data.get("dist/preload.js", b"").decode("utf-8", errors="replace")
    updater = files_data.get("dist/updater.js", b"").decode("utf-8", errors="replace")
    return (PATCH_SIGNATURE in preload) or (UPDATER_HOOK_SIGNATURE in updater)


def strip_existing_patches(files_data):
    stripped = False
    if "dist/preload.js" in files_data:
        preload = files_data["dist/preload.js"].decode("utf-8")
        idx = preload.find(PATCH_SIGNATURE)
        if idx != -1:
            preload = preload[:idx].rstrip() + "\n"
            files_data["dist/preload.js"] = preload.encode("utf-8")
            stripped = True
    if "dist/updater.js" in files_data:
        updater = files_data["dist/updater.js"].decode("utf-8")
        idx = updater.find(UPDATER_HOOK_SIGNATURE)
        if idx != -1:
            updater = updater[:idx].rstrip() + "\n"
            files_data["dist/updater.js"] = updater.encode("utf-8")
            stripped = True
    return stripped


def apply_patch(files_data):
    if is_patched(files_data):
        print("[*] ASAR is already patched with ANTIGRAVITY_TR_PATCH_V1.")
        return False

    with open(LOCALE_SCRIPT_PATH, "r", encoding="utf-8") as f:
        locale_code = f.read()

    # 1. Patch dist/preload.js
    preload = files_data["dist/preload.js"].decode("utf-8")
    preload += "\n\n" + PATCH_SIGNATURE + "\n" + locale_code + "\n"
    files_data["dist/preload.js"] = preload.encode("utf-8")

    # 2. Patch dist/menu.js
    if "dist/menu.js" in files_data:
        menu = files_data["dist/menu.js"].decode("utf-8")
        menu = menu.replace("label: 'New Window'", "label: 'Yeni Pencere'")
        menu = menu.replace("label: 'Docs'", "label: 'Belgeler'")
        menu = menu.replace("label: 'Connect to WSL'", "label: 'WSL\\'ye Bağlan'")
        menu = menu.replace("label: 'Reopen Locally'", "label: 'Yerel Olarak Yeniden Aç'")
        files_data["dist/menu.js"] = menu.encode("utf-8")

    # 3. Patch dist/tray.js
    if "dist/tray.js" in files_data:
        tray = files_data["dist/tray.js"].decode("utf-8")
        old_pattern = (
            "countItem.label =\n"
            "                (count > 0 ? `${count}` : 'No') +\n"
            "                    ' agent' +\n"
            "                    (count === 1 ? '' : 's') +\n"
            "                    ' running';"
        )
        new_pattern = (
            "countItem.label =\n"
            "                (count > 0 ? `${count} ajan çalışıyor` : 'Çalışan ajan yok');"
        )
        tray = tray.replace(old_pattern, new_pattern)
        files_data["dist/tray.js"] = tray.encode("utf-8")

    # 4. Patch dist/updater.js (UI strings + one-shot update addon hook)
    if "dist/updater.js" in files_data:
        updater = files_data["dist/updater.js"].decode("utf-8")
        updater = updater.replace('MenuUpdateStep["CheckForUpdates"] = "Check for Updates"', 'MenuUpdateStep["CheckForUpdates"] = "Güncellemeleri Denetle"')
        updater = updater.replace('MenuUpdateStep["CheckingForUpdates"] = "Checking for Updates..."', 'MenuUpdateStep["CheckingForUpdates"] = "Güncellemeler Denetleniyor..."')
        updater = updater.replace('MenuUpdateStep["DownloadingUpdate"] = "Downloading Update..."', 'MenuUpdateStep["DownloadingUpdate"] = "Güncelleme İndiriliyor..."')
        updater = updater.replace('MenuUpdateStep["RestartToUpdate"] = "Restart to Update"', 'MenuUpdateStep["RestartToUpdate"] = "Güncellemek için Yeniden Başlat"')
        updater = updater.replace("title: 'Check for Updates'", "title: 'Güncellemeleri Denetle'")
        updater = updater.replace("message: 'No updates available'", "message: 'Kullanılabilir güncelleme yok'")
        updater = updater.rstrip() + "\n\n" + build_updater_hook()
        files_data["dist/updater.js"] = updater.encode("utf-8")

    # 5. Patch dist/main.js
    if "dist/main.js" in files_data:
        main = files_data["dist/main.js"].decode("utf-8")
        main = main.replace("label: 'No agents running'", "label: 'Çalışan ajan yok'")
        main = main.replace("label: 'Quit'", "label: 'Çıkış'")
        main = main.replace("title: 'Confirm Quit'", "title: 'Çıkışı Onayla'")
        main = main.replace("message: 'Are you sure you want to quit?'", "message: 'Çıkmak istediğinizden emin misiniz?'")
        main = main.replace("detail: 'There may be agents or background tasks running.'", "detail: 'Çalışan ajanlar veya arka plan görevleri olabilir.'")
        main = main.replace("buttons: ['Cancel', 'Quit']", "buttons: ['İptal', 'Çıkış']")
        main = main.replace("label: `Open ${electron_1.app.getName()}`", "label: `${electron_1.app.getName()}'yi Aç`")
        files_data["dist/main.js"] = main.encode("utf-8")

    print("[+] Turkish translation patch injected into memory.")
    return True


def backup_asar(asar_path, version):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ext_bak = f"{asar_path}.bak.{version}"
    tool_bak = os.path.join(BACKUP_DIR, f"app.asar.bak.{version}")

    if not os.path.exists(ext_bak):
        print(f"[+] Creating backup: {ext_bak}")
        shutil.copy2(asar_path, ext_bak)
    if not os.path.exists(tool_bak):
        print(f"[+] Creating persistent backup: {tool_bak}")
        shutil.copy2(asar_path, tool_bak)


def restore_asar(asar_path):
    # Find most recent backup
    candidates = []
    parent = os.path.dirname(asar_path)
    for name in os.listdir(parent):
        if name.startswith("app.asar.bak."):
            candidates.append(os.path.join(parent, name))
    if not candidates and os.path.exists(BACKUP_DIR):
        for name in os.listdir(BACKUP_DIR):
            if name.startswith("app.asar.bak."):
                candidates.append(os.path.join(BACKUP_DIR, name))

    if not candidates:
        print("[-] No backup file found to restore!")
        return False

    candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    best_backup = candidates[0]
    print(f"[+] Restoring {asar_path} from {best_backup}")
    shutil.copy2(best_backup, asar_path)
    if os.path.exists(STAMP_FILE_PATH):
        os.remove(STAMP_FILE_PATH)
    print("[+] Restore completed successfully.")
    return True


def check_patch(asar_path):
    if not os.path.exists(asar_path):
        print(f"[-] File not found: {asar_path}")
        return False
    header, files_data = read_asar(asar_path)
    ver = get_version(files_data)
    patched = is_patched(files_data)
    print(f"[*] Antigravity version: {ver}")
    print(f"[*] Turkish Patch status: {'PATCHED' if patched else 'NOT PATCHED'}")
    return patched


def patch_file(asar_path, force=False, dry_run=False):
    print(f"[*] Reading ASAR: {asar_path}")
    header, files_data = read_asar(asar_path)
    ver = get_version(files_data)
    print(f"[*] App version: {ver}")

    patched = is_patched(files_data)

    if patched and not force:
        print("[*] ASAR is already patched. Nothing to do.")
        return True

    # Backup original clean version only if NO prior patch signatures exist
    if not has_any_patch(files_data):
        backup_asar(asar_path, ver)

    # Strip old/partial patches before applying current patch cleanly
    if force or has_any_patch(files_data):
        if strip_existing_patches(files_data):
            print("[*] Existing patch signatures stripped for clean re-patching.")

    if not apply_patch(files_data):
        return True

    temp_out = os.path.join(TEMP_DIR, f"app.asar.patched.{os.getpid()}")
    print(f"[*] Writing patched ASAR to temporary file: {temp_out}")
    write_asar(temp_out, header, files_data)

    # Verify temp ASAR
    print("[*] Verifying repacked ASAR integrity...")
    test_header, test_files = read_asar(temp_out)
    if not is_patched(test_files):
        raise RuntimeError("Verification failed: signature missing in repacked ASAR!")
    print(f"[+] Verified: {len(test_files)} files intact.")

    if dry_run:
        print("[*] Dry run requested. Not replacing original app.asar.")
        os.remove(temp_out)
        return True

    print(f"[+] Replacing {asar_path} with patched ASAR...")
    try:
        shutil.move(temp_out, asar_path)
        if os.path.exists(STAMP_FILE_PATH):
            os.remove(STAMP_FILE_PATH)
        print("[+] Success: Antigravity Turkish patch applied successfully!")
        return True
    except PermissionError:
        print("[-] PermissionError: app.asar is currently locked by a running Antigravity process.")
        print(f"[*] The patched file is saved at: {temp_out}")
        print("[*] File will be updated when the process releases the file.")
        return False


def main():
    parser = argparse.ArgumentParser(description="Antigravity Turkish Language Patcher")
    parser.add_argument("--asar", default=DEFAULT_ASAR, help="Path to app.asar")
    parser.add_argument("--check", action="store_true", help="Check patch status")
    parser.add_argument("--restore", action="store_true", help="Restore original app.asar from backup")
    parser.add_argument("--force", action="store_true", help="Force re-patch using latest locale scripts")
    parser.add_argument("--dry-run", action="store_true", help="Simulate patch without writing")
    args = parser.parse_args()

    if args.check:
        sys.exit(0 if check_patch(args.asar) else 1)
    elif args.restore:
        sys.exit(0 if restore_asar(args.asar) else 1)
    else:
        sys.exit(0 if patch_file(args.asar, force=args.force, dry_run=args.dry_run) else 1)


if __name__ == "__main__":
    main()