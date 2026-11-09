#!/usr/bin/env python
"""Detect the local creative toolchain and print a portable manifest.

    python detect_tools.py            # human table
    python detect_tools.py --json     # machine readable
    python detect_tools.py --write    # write tools.json next to this script

Environment variables recognised by the other scripts:

    DSH_PYTHON   python used for pptx work (python-pptx/lxml/Pillow/pypdf)
    ALT_PYTHON   python with the image/number stack (matplotlib/cv2/torch)
    BLENDER_EXE  path to blender.exe
    COMFYUI      ComfyUI home directory (contains draw.cmd / draw.ps1)
    PPT          path to POWERPNT.EXE (optional)
"""
import argparse
import json
import os
import shutil
import subprocess
import sys


def which(name):
    p = shutil.which(name)
    return p


def first_existing(paths):
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None


def find_blender():
    cands = [os.environ.get("BLENDER_EXE")]
    for root in (r"C:\Program Files\Blender Foundation", r"C:\Program Files", r"D:\Program Files"):
        if os.path.isdir(root):
            for dirpath, dirnames, filenames in os.walk(root):
                if dirpath.count(os.sep) - root.count(os.sep) > 3:
                    dirnames[:] = []
                    continue
                if "blender.exe" in filenames:
                    cands.append(os.path.join(dirpath, "blender.exe"))
    return first_existing(cands)


def find_comfyui():
    cands = [os.environ.get("COMFYUI")]
    for drive in ("C:\\", "D:\\", "E:\\", "F:\\"):
        if os.path.isdir(drive):
            for name in os.listdir(drive):
                if name.lower().startswith("comfyui"):
                    cands.append(os.path.join(drive, name))
    for c in cands:
        if c and (os.path.exists(os.path.join(c, "draw.cmd")) or
                  os.path.exists(os.path.join(c, "main.py"))):
            return c
    return None


def find_powerpoint():
    if os.environ.get("PPT") and os.path.exists(os.environ["PPT"]):
        return os.environ["PPT"]
    for root in (r"C:\Program Files\Microsoft Office", r"C:\Program Files (x86)\Microsoft Office"):
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            if "POWERPNT.EXE" in filenames:
                return os.path.join(dirpath, "POWERPNT.EXE")
    return None


def python_has(py, mods):
    if not py or not os.path.exists(py):
        return []
    try:
        out = subprocess.run([py, "-c", "import importlib.util as u,sys;print(' '.join(m for m in %r if u.find_spec(m)))" % (mods,)],
                             capture_output=True, text=True, timeout=30)
        return out.stdout.split()
    except Exception:
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    dsh_py = os.environ.get("DSH_PYTHON") or first_existing([
        os.path.expandvars(r"%USERPROFILE%\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe")])
    alt_py = os.environ.get("ALT_PYTHON") or first_existing([r"%ALT_PYTHON%"])
    if not alt_py and which("python"):
        alt_py = which("python")

    blender = find_blender()
    comfy = find_comfyui()
    ppt = find_powerpoint()

    manifest = {
        "python_pptx": {"path": dsh_py, "modules": python_has(dsh_py, ["pptx", "lxml", "PIL", "numpy", "pypdf"])},
        "python_alt": {"path": alt_py, "modules": python_has(alt_py, ["matplotlib", "cv2", "torch"])},
        "blender": {"path": blender, "version": None},
        "comfyui": {"home": comfy, "draw_cmd": os.path.join(comfy, "draw.cmd") if comfy else None},
        "ffmpeg": {"path": which("ffmpeg")},
        "ffprobe": {"path": which("ffprobe")},
        "powerpoint": {"path": ppt},
        "env": {k: os.environ.get(k) for k in ("DSH_PYTHON", "ALT_PYTHON", "BLENDER_EXE", "COMFYUI", "PPT") if os.environ.get(k)},
    }
    if blender:
        try:
            out = subprocess.run([blender, "--version"], capture_output=True, text=True, timeout=60)
            manifest["blender"]["version"] = (out.stdout or "").splitlines()[0] if out.stdout else None
        except Exception:
            pass

    if args.write:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        print("wrote", path)

    if args.json:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return

    print("%-14s %s" % ("tool", "status"))
    print("%-14s %s" % ("python_pptx", (manifest["python_pptx"]["path"] or "-") + "  [" + ", ".join(manifest["python_pptx"]["modules"]) + "]"))
    print("%-14s %s" % ("python_alt", (manifest["python_alt"]["path"] or "-") + "  [" + ", ".join(manifest["python_alt"]["modules"]) + "]"))
    print("%-14s %s" % ("blender", (manifest["blender"]["path"] or "-") + "  " + str(manifest["blender"]["version"] or "")))
    print("%-14s %s" % ("comfyui", manifest["comfyui"]["home"] or "-"))
    print("%-14s %s" % ("ffmpeg", manifest["ffmpeg"]["path"] or "-"))
    print("%-14s %s" % ("powerpoint", manifest["powerpoint"]["path"] or "-"))
    missing = []
    if not manifest["python_pptx"]["path"]:
        missing.append("python-pptx runtime")
    if not manifest["powerpoint"]["path"]:
        missing.append("PowerPoint (needed for the export/audit loop)")
    if missing:
        print("\nmissing:", ", ".join(missing))
        print("Ask the user before installing anything; see references/09-local-tools.md.")


if __name__ == "__main__":
    main()
