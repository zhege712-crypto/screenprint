#!/usr/bin/env python
"""Inventory a .pptx: slides, text runs, charts, media, animations.

Usage:
    python pptx_probe.py deck.pptx                 # human report
    python pptx_probe.py deck.pptx --json out.json # machine report
"""
import argparse
import collections
import json
import re
import zipfile

from lxml import etree as E

P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
C = "{http://schemas.openxmlformats.org/drawingml/2006/chart}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
NS = {"p": P[1:-1], "a": A[1:-1], "c": C[1:-1]}


def slide_parts(z):
    pres = E.fromstring(z.read("ppt/presentation.xml"))
    rels = {x.get("Id"): x.get("Target")
            for x in E.fromstring(z.read("ppt/_rels/presentation.xml.rels"))}
    parts = []
    for sid in pres.findall("p:sldIdLst/p:sldId", NS):
        rid = sid.get(R + "id")
        target = rels[rid]
        parts.append(target.lstrip("/") if target.startswith("/")
                     else "ppt/" + target.replace("../", ""))
    return parts


def shape_text(el):
    return "".join(t.text or "" for t in el.iter(A + "t")).strip()


def probe(path):
    z = zipfile.ZipFile(path)
    assert z.testzip() is None, "corrupt zip"
    parts = slide_parts(z)
    out = {"file": path, "slides": len(parts), "pages": [], "media": []}

    for i, part in enumerate(parts, 1):
        root = E.fromstring(z.read(part))
        page = {
            "page": i,
            "hidden": root.get("show") == "0",
            "clicks": len(root.xpath('.//p:cTn[@nodeType="mainSeq"]//p:cTn[@nodeType="clickEffect"]',
                                    namespaces=NS)),
            "effects": len(root.xpath('.//p:cTn[@nodeType="mainSeq"]//p:cTn'
                                      '[@nodeType="clickEffect" or @nodeType="withEffect"]',
                                      namespaces=NS)),
            "rise": len(root.xpath('.//p:anim/p:cBhvr/p:attrNameLst/p:attrName[text()="ppt_y"]',
                                   namespaces=NS)),
            "videos": len(list(root.iter(P + "video"))),
            "charts": [],
            "tables": len(list(root.iter(A + "tbl"))),
            "text": shape_text(root)[:120],
        }
        for bld in root.iter(P + "bldGraphic"):
            sub = bld.find(P + "bldSub")
            chart = sub.find(A + "bldChart") if sub is not None else None
            page.setdefault("builds", []).append(
                {"spid": bld.get("spid"), "bld": chart.get("bld") if chart is not None else "asOne"})
        for gf in root.iter(P + "graphicFrame"):
            ch = gf.find(".//" + C + "chart")
            if ch is not None:
                page["charts"].append({"rid": ch.get(R + "embed") or ch.get(R + "id")})
        out["pages"].append(page)

    for name in z.namelist():
        if name.startswith("ppt/media/"):
            out["media"].append({"part": name, "bytes": len(z.read(name))})

    out["click_groups_total"] = sum(p["clicks"] for p in out["pages"])
    out["hidden_pages"] = [p["page"] for p in out["pages"] if p["hidden"]]
    return out


def report(d):
    print("file :", d["file"])
    print("slides:", d["slides"], "| hidden:", d["hidden_pages"],
          "| click groups:", d["click_groups_total"])
    print("media :", len(d["media"]), "parts,",
          sum(m["bytes"] for m in d["media"]) // 1024, "KB")
    print()
    print("%3s %-6s %-6s %-6s %-6s %-6s %s" % ("pg", "hidden", "click", "fx", "video", "chart", "text"))
    for p in d["pages"]:
        print("%3d %-6s %-6d %-6d %-6d %-6d %s" % (
            p["page"], "y" if p["hidden"] else "", p["clicks"], p["effects"],
            p["videos"], len(p["charts"]), re.sub(r"\s+", " ", p["text"])[:46]))
        for b in p.get("builds", []):
            if b["bld"] != "asOne":
                print("      build: spid=%s bld=%s" % (b["spid"], b["bld"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pptx")
    ap.add_argument("--json")
    args = ap.parse_args()
    d = probe(args.pptx)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        print("wrote", args.json)
    report(d)


if __name__ == "__main__":
    main()
