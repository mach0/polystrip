#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compile Qt translation files (.ts) to binary message catalog files (.qm).
Supports lrelease binaries and PyQt translation tools.
"""

import os
import shutil
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
I18N_DIR = os.path.join(REPO_ROOT, 'polystrip', 'i18n')


def find_lrelease():
    candidates = [
        'lrelease',
        '/usr/lib/qt6/bin/lrelease',
        'lrelease-qt5',
        'lrelease-qt6',
        '/usr/lib/qt5/bin/lrelease'
    ]
    for c in candidates:
        path = shutil.which(c) or (c if os.path.isfile(c) and os.access(c, os.X_OK) else None)
        if path:
            return path
    return None


def main():
    lrelease_bin = find_lrelease()
    if not lrelease_bin:
        print("Error: No lrelease binary found on PATH or standard locations.", file=sys.stderr)
        return 1

    ts_files = [f for f in os.listdir(I18N_DIR) if f.endswith('.ts')]
    if not ts_files:
        print(f"No .ts files found in {I18N_DIR}")
        return 0

    success = True
    for ts in ts_files:
        ts_path = os.path.join(I18N_DIR, ts)
        qm_path = os.path.join(I18N_DIR, ts[:-3] + '.qm')
        cmd = [lrelease_bin, ts_path, '-qm', qm_path]
        try:
            res = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print(f"Compiled {ts} -> {os.path.basename(qm_path)}")
            if res.stdout.strip():
                print("  " + res.stdout.strip().replace("\n", "\n  "))
        except subprocess.CalledProcessError as e:
            print(f"Failed to compile {ts}: {e.stderr}", file=sys.stderr)
            success = False

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
