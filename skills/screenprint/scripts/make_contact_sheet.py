#!/usr/bin/env python
"""Build contact sheets and before/after sheets from rendered slide PNGs.

Usage:
    python make_contact_sheet.py build/native_v39 --out PREVIEW_v39.png --pages 1,3,5,10,15,21
    python make_contact_sheet.py old_dir new_dir --out BEFORE_AFTER.png --pages 15 --labels v38,v39
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw

CELL = (528, 297)          # 3x2 grid inside 1600x900
BIG = (760, 428)           # side-by-side comparison cell


def page_files(folder):
    return sorted(f for f in os.listdir(folder) if f.lower().endswith(".png"))


def contact(folder, pages, out):
    files = page_files(folder)
    if not pages:
        pages = list(range(1, len(files) + 1))
    cols = 3
    rows = (len(pages) + cols - 1) // cols
    sheet = Image.new("RGB", (1600, 306 * rows + 8), "white")
    for i, page in enumerate(pages):
        f = os.path.join(folder, "p%02d.png" % page)
        if not os.path.exists(f):
            print("missing", f)
            continue
        img = Image.open(f).convert("RGB").resize(CELL, Image.LANCZOS)
        x = 8 + (i % cols) * (CELL[0] + 4)
        y = 8 + (i // cols) * 306
        sheet.paste(img, (x, y))
    sheet.save(out)
    print("wrote", out, sheet.size)


def before_after(old_dir, new_dir, pages, out, labels):
    rows = len(pages)
    sheet = Image.new("RGB", (BIG[0] * 2 + 32, (BIG[1] + 26) * rows + 12), "white")
    d = ImageDraw.Draw(sheet)
    for r, page in enumerate(pages):
        y = 12 + r * (BIG[1] + 26)
        for c, folder in enumerate((old_dir, new_dir)):
            f = os.path.join(folder, "p%02d.png" % page)
            if not os.path.exists(f):
                print("missing", f)
                continue
            img = Image.open(f).convert("RGB").resize(BIG, Image.LANCZOS)
            x = 12 + c * (BIG[0] + 8)
            sheet.paste(img, (x, y + 18))
            d.text((x, y + 2), "%s  p%02d" % (labels[c], page), fill=(20, 40, 55))
    sheet.save(out)
    print("wrote", out, sheet.size)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("new_folder", nargs="?")
    ap.add_argument("--out", required=True)
    ap.add_argument("--pages", default="")
    ap.add_argument("--labels", default="before,after")
    args = ap.parse_args()
    pages = [int(p) for p in args.pages.split(",") if p.strip()]
    if args.new_folder:
        before_after(args.folder, args.new_folder, pages, args.out, args.labels.split(","))
    else:
        contact(args.folder, pages, args.out)


if __name__ == "__main__":
    sys.exit(main())
