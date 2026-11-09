#!/usr/bin/env python
"""Layout sanity checks: bleed, off-slide shapes, text overflow, overlaps, rails.

Usage:
    python layout_audit.py deck.pptx
    python layout_audit.py deck.pptx --rail-top 6480000 --margin 300000
"""
import argparse
import math
import zipfile

from lxml import etree as E

P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
NS = {"p": P[1:-1], "a": A[1:-1]}
W, H = 12192000, 6858000
EMU_PT = 12700.0


def slide_parts(z):
    pres = E.fromstring(z.read("ppt/presentation.xml"))
    rels = {x.get("Id"): x.get("Target")
            for x in E.fromstring(z.read("ppt/_rels/presentation.xml.rels"))}
    out = []
    for sid in pres.findall("p:sldIdLst/p:sldId", NS):
        t = rels[sid.get(R + "id")]
        out.append(t.lstrip("/") if t.startswith("/") else "ppt/" + t.replace("../", ""))
    return out


def elements(root):
    for el in root.iter():
        if E.QName(el).localname not in ("sp", "pic", "graphicFrame", "grpSp"):
            continue
        nv = el.find(".//" + P + "cNvPr")
        if nv is None:
            continue
        xf = el.find(P + "spPr/" + A + "xfrm")
        if xf is None:
            xf = el.find(P + "grpSpPr/" + A + "xfrm")
        if xf is None:
            xf = el.find(P + "xfrm")
        if xf is None:
            continue
        off, ext = xf.find(A + "off"), xf.find(A + "ext")
        if off is None or ext is None:
            continue
        txt = "".join(t.text or "" for t in el.iter(A + "t")).strip()
        sizes = [int(rp.get("sz")) / 100.0 for rp in el.iter(A + "rPr") if rp.get("sz")]
        yield {
            "name": nv.get("name"),
            "box": (int(off.get("x")), int(off.get("y")), int(ext.get("cx")), int(ext.get("cy"))),
            "text": txt,
            "size": max(sizes) if sizes else 18.0,
        }


def est_lines(text, cx, size_pt):
    per_line = max(4, int((cx / EMU_PT) / (size_pt * 0.52)))
    return sum(max(1, math.ceil(len(p) / per_line)) for p in text.split("\n"))


def audit(path, rail_top, margin):
    z = zipfile.ZipFile(path)
    problems = []
    for i, part in enumerate(slide_parts(z), 1):
        root = E.fromstring(z.read(part))
        items = list(elements(root))
        full_bleed = [it for it in items
                      if it["box"][2] >= W - 10000 and it["box"][3] >= H - 10000]
        for it in full_bleed:
            if it["box"][:2] != (0, 0):
                problems.append((i, "bleed", it["name"], it["box"]))
        for it in items:
            x, y, cx, cy = it["box"]
            if cx <= 0 or cy <= 0:
                problems.append((i, "zero-size", it["name"], it["box"]))
            elif x + cx <= 0 or y + cy <= 0 or x >= W or y >= H:
                problems.append((i, "off-slide", it["name"], it["box"]))
            if it["text"]:
                need = est_lines(it["text"], cx, it["size"]) * it["size"] * 1.22 * EMU_PT
                if need > cy * 1.12 and cy > 0:
                    problems.append((i, "overflow?", it["name"], (cx, cy, int(need))))
                if y + cy > rail_top + margin and it["size"] > 14:
                    problems.append((i, "into-rail", it["name"], it["box"]))
        texts = [it for it in items if it["text"]]
        for a in range(len(texts)):
            for b in range(a + 1, len(texts)):
                ax, ay, acx, acy = texts[a]["box"]
                bx, by, bcx, bcy = texts[b]["box"]
                ix = max(0, min(ax + acx, bx + bcx) - max(ax, bx))
                iy = max(0, min(ay + acy, by + bcy) - max(ay, by))
                small = min(acx * acy, bcx * bcy)
                if small and ix * iy / small > 0.25:
                    problems.append((i, "text-overlap", texts[a]["name"] + " x " + texts[b]["name"],
                                     int(100 * ix * iy / small)))

    if not problems:
        print("no layout problems found")
        return problems
    print("%3s %-14s %-40s %s" % ("pg", "kind", "shape", "detail"))
    for pg, kind, name, detail in problems:
        print("%3d %-14s %-40s %s" % (pg, kind, (name or "")[:40], detail))
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pptx")
    ap.add_argument("--rail-top", type=int, default=6480000)
    ap.add_argument("--margin", type=int, default=0)
    args = ap.parse_args()
    audit(args.pptx, args.rail_top, args.margin)


if __name__ == "__main__":
    main()
