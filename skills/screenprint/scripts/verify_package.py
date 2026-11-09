#!/usr/bin/env python
"""Structural audit of a deck, optionally against a reference deck.

Usage:
    python verify_package.py deck.pptx --expect-slides 30 --expect-clicks 43
    python verify_package.py deck.pptx --ref previous.pptx --json audit.json
"""
import argparse
import hashlib
import json
import re
import zipfile

from lxml import etree as E

P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
NS = {"p": P[1:-1], "a": A[1:-1]}


def load(path):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None, "corrupt zip"
        return {n: z.read(n) for n in z.namelist()}


def slide_parts(pkg):
    pres = E.fromstring(pkg["ppt/presentation.xml"])
    rels = {x.get("Id"): x.get("Target")
            for x in E.fromstring(pkg["ppt/_rels/presentation.xml.rels"])}
    out = []
    for sid in pres.findall("p:sldIdLst/p:sldId", NS):
        t = rels[sid.get(R + "id")]
        out.append(t.lstrip("/") if t.startswith("/") else "ppt/" + t.replace("../", ""))
    return out


def text_of(blob):
    root = E.fromstring(blob)
    return re.sub(r"\s+", "", "".join(root.xpath(".//a:t/text()", namespaces=NS)))


def audit(path, ref=None, expect_slides=None, expect_clicks=None):
    pkg = load(path)
    parts = slide_parts(pkg)
    rep = {
        "file": path,
        "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest(),
        "bytes": len(open(path, "rb").read()),
        "slides": len(parts),
        "hidden_pages": [],
        "clicks": {},
        "effects": 0,
        "videos": len([n for n in pkg if n.endswith(".mp4")]),
        "media_parts": len([n for n in pkg if n.startswith("ppt/media/")]),
        "chart_builds": {},
        "looped_media": 0,
    }
    for i, part in enumerate(parts, 1):
        root = E.fromstring(pkg[part])
        if root.get("show") == "0":
            rep["hidden_pages"].append(i)
        clicks = len(root.xpath('.//p:cTn[@nodeType="mainSeq"]//p:cTn[@nodeType="clickEffect"]',
                                namespaces=NS))
        rep["clicks"][i] = clicks
        rep["effects"] += len(root.xpath('.//p:cTn[@nodeType="mainSeq"]'
                                         '//p:cTn[@nodeType="clickEffect" or @nodeType="withEffect"]',
                                         namespaces=NS))
        rep["looped_media"] += len(root.xpath('.//p:cTn[@repeatCount="indefinite"]', namespaces=NS))
        builds = [b.get("bld") for b in root.iter(A + "bldChart")]
        if builds:
            rep["chart_builds"][i] = builds
    rep["click_groups_total"] = sum(rep["clicks"].values())

    if ref:
        old = load(ref)
        oparts = slide_parts(old)
        changed = [i for i, (a, b) in enumerate(zip(parts, oparts), 1)
                   if text_of(pkg[a]) != text_of(old[b])]
        rep["text_changed_pages"] = changed
        rep["text_identical"] = not changed and len(parts) == len(oparts)
        rep["media_changed"] = sorted(
            n for n in pkg
            if n.startswith("ppt/media/")
            and hashlib.sha256(pkg[n]).hexdigest()
            != hashlib.sha256(old.get(n, b"")).hexdigest())

    ok = True
    if expect_slides is not None and rep["slides"] != expect_slides:
        print("FAIL slides %d != %d" % (rep["slides"], expect_slides))
        ok = False
    if expect_clicks is not None and rep["click_groups_total"] != expect_clicks:
        print("FAIL clicks %d != %d" % (rep["click_groups_total"], expect_clicks))
        ok = False
    if ref and not rep["text_identical"]:
        print("WARN text differs on pages", rep.get("text_changed_pages"))
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    print("OK" if ok else "PROBLEMS FOUND")
    return rep, ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pptx")
    ap.add_argument("--ref")
    ap.add_argument("--expect-slides", type=int)
    ap.add_argument("--expect-clicks", type=int)
    ap.add_argument("--json")
    args = ap.parse_args()
    rep, _ = audit(args.pptx, args.ref, args.expect_slides, args.expect_clicks)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=2)
        print("wrote", args.json)


if __name__ == "__main__":
    main()
