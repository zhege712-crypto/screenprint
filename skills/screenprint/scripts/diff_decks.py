#!/usr/bin/env python
"""Diff two decks: text edits, shape geometry, colours, media, click counts.

Usage:
    python diff_decks.py old.pptx new.pptx            # report
    python diff_decks.py old.pptx new.pptx --json d.json
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


def plain_text(blob):
    return "".join(t.text or "" for t in E.fromstring(blob).iter(A + "t"))


def boxes(root):
    out = {}
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
        out[nv.get("name")] = (int(off.get("x")), int(off.get("y")),
                               int(ext.get("cx")), int(ext.get("cy")))
    return out


def run_styles(root):
    out = {}
    for r in root.iter(A + "r"):
        t = r.find(A + "t")
        rp = r.find(A + "rPr")
        if t is None or not (t.text or "").strip():
            continue
        clr = rp.find(A + "solidFill/" + A + "srgbClr") if rp is not None else None
        out[t.text.strip()[:32]] = (
            rp.get("sz") if rp is not None else None,
            rp.get("b") if rp is not None else None,
            clr.get("val") if clr is not None else None,
        )
    return out


def diff(old_path, new_path):
    old, new = load(old_path), load(new_path)
    oparts, nparts = slide_parts(old), slide_parts(new)
    rep = {"old": old_path, "new": new_path, "pages": {}, "media": {}}
    for i, (op, np_) in enumerate(zip(oparts, nparts), 1):
        a, b = E.fromstring(old[op]), E.fromstring(new[np_])
        page = {}
        ta, tb = plain_text(old[op]), plain_text(new[np_])
        if re.sub(r"\s+", "", ta) != re.sub(r"\s+", "", tb):
            k = next((j for j in range(min(len(ta), len(tb))) if ta[j] != tb[j]),
                     min(len(ta), len(tb)))
            page["text"] = {"at": k, "old": ta[max(0, k - 40):k + 80], "new": tb[max(0, k - 40):k + 80]}
        ba, bb = boxes(a), boxes(b)
        moved = {k: {"old": ba[k], "new": bb[k]} for k in ba if k in bb and ba[k] != bb[k]}
        if moved:
            page["moved"] = moved
        added = [k for k in bb if k not in ba]
        removed = [k for k in ba if k not in bb]
        if added or removed:
            page["added"], page["removed"] = added, removed
        ra, rb = run_styles(a), run_styles(b)
        recoloured = {k: {"old": ra[k], "new": rb[k]} for k in ra if k in rb and ra[k] != rb[k]}
        if recoloured:
            page["restyled"] = recoloured
        ca = len(a.xpath('.//p:cTn[@nodeType="mainSeq"]//p:cTn[@nodeType="clickEffect"]', namespaces=NS))
        cb = len(b.xpath('.//p:cTn[@nodeType="mainSeq"]//p:cTn[@nodeType="clickEffect"]', namespaces=NS))
        if ca != cb:
            page["clicks"] = {"old": ca, "new": cb}
        if page:
            rep["pages"][i] = page

    for n in sorted(set(old) | set(new)):
        if not n.startswith("ppt/media/"):
            continue
        ha = hashlib.sha256(old.get(n, b"")).hexdigest()
        hb = hashlib.sha256(new.get(n, b"")).hexdigest()
        if ha != hb:
            rep["media"][n] = {"old": ha[:16], "new": hb[:16],
                              "old_bytes": len(old.get(n, b"")), "new_bytes": len(new.get(n, b""))}
    return rep


def report(d):
    if not d["pages"] and not d["media"]:
        print("no differences")
        return
    for page, changes in sorted(d["pages"].items()):
        print("slide %d" % page)
        if "text" in changes:
            print("   text changed at %d:" % changes["text"]["at"])
            print("     old:", changes["text"]["old"])
            print("     new:", changes["text"]["new"])
        for k, v in list(changes.get("moved", {}).items())[:10]:
            print("   moved  %-28s %s -> %s" % (k[:28], v["old"], v["new"]))
        for k, v in list(changes.get("restyled", {}).items())[:10]:
            print("   style  %-28s %s -> %s" % (k[:28], v["old"], v["new"]))
        if changes.get("added"):
            print("   added  ", changes["added"][:6])
        if changes.get("removed"):
            print("   removed", changes["removed"][:6])
        if changes.get("clicks"):
            print("   clicks %d -> %d" % (changes["clicks"]["old"], changes["clicks"]["new"]))
    if d["media"]:
        print("media changed:")
        for n, v in d["media"].items():
            print("   %-28s %8d -> %8d bytes" % (n, v["old_bytes"], v["new_bytes"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--json")
    args = ap.parse_args()
    d = diff(args.old, args.new)
    report(d)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        print("wrote", args.json)


if __name__ == "__main__":
    main()
