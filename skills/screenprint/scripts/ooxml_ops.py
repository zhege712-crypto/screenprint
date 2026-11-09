#!/usr/bin/env python
"""OOXML operations on a .pptx that python-pptx does not expose.

Subcommands
    chart-build   give a chart a build animation (category / series / all)
    wipe          replace a shape's entrance effect with a wipe
    media-loop    set repeatCount="indefinite" on every video on a slide
    recolor       map srgbClr values across the whole deck
    replace-media replace a media/poster part by name
    move          shift shapes by name or text prefix on given slides
    bld-report    print chart build state per slide

Examples
    python ooxml_ops.py chart-build deck.pptx --slide 10 --shape-id 5 --mode category --wipe right
    python ooxml_ops.py media-loop deck.pptx --slide 5
    python ooxml_ops.py recolor deck.pptx --map 647681=4C5D66 --map A9C6D4=4F6B78
    python ooxml_ops.py move deck.pptx --slide 5 --text "Blue: follower" --dy -294000
"""
import argparse
import os
import re
import shutil
import zipfile

from lxml import etree as E

P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
C = "{http://schemas.openxmlformats.org/drawingml/2006/chart}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
NS = {"p": P[1:-1], "a": A[1:-1], "c": C[1:-1]}


# ---------------------------------------------------------------- plumbing
def read(path):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None, "corrupt zip"
        names = z.namelist()
        return names, {n: z.read(n) for n in names}


def write(path, names, data):
    tmp = path + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.writestr(n, data[n])
    os.replace(tmp, path)


def slide_part(n):
    return "ppt/slides/slide%d.xml" % n


def parse(data, part):
    return E.fromstring(data[part])


def store(data, part, root):
    data[part] = E.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def shapes(root):
    for el in root.iter():
        if E.QName(el).localname not in ("sp", "pic", "graphicFrame", "grpSp"):
            continue
        nv = el.find(".//" + P + "cNvPr")
        if nv is not None:
            yield el, nv


# ---------------------------------------------------------------- commands
def cmd_chart_build(args):
    names, data = read(args.pptx)
    part = slide_part(args.slide)
    root = parse(data, part)
    mode, target = args.mode, None
    for bld in root.iter(P + "bldGraphic"):
        if bld.get("spid") == str(args.shape_id):
            target = bld
    if target is None:
        lst = root.find(".//" + P + "bldLst")
        assert lst is not None, "slide has no bldLst; no chart animation container"
        target = E.SubElement(lst, P + "bldGraphic")
        target.set("spid", str(args.shape_id))
        target.set("grpId", "0")
    for child in list(target):
        target.remove(child)
    sub = E.SubElement(target, P + "bldSub")
    E.SubElement(sub, A + "bldChart").set("bld", mode)
    if args.wipe:
        wipe_effect(root, args.shape_id, args.wipe)
    store(data, part, root)
    write(args.pptx, names, data)
    print("chart build set: slide %d spid %s -> %s%s"
          % (args.slide, args.shape_id, mode, "" if not args.wipe else " + wipe(%s)" % args.wipe))


def wipe_effect(root, shape_id, direction):
    direction = {"up": "wipe(up)", "down": "wipe(down)",
                 "left": "wipe(left)", "right": "wipe(right)"}.get(direction, direction)
    direction = direction if direction.startswith("wipe(") else "wipe(%s)" % direction
    touched = 0
    for ctn in root.iter(P + "cTn"):
        if ctn.get("nodeType") not in ("clickEffect", "withEffect", "afterEffect"):
            continue
        tgt = ctn.find(".//" + P + "tgtEl/" + P + "spTgt")
        if tgt is None or tgt.get("spid") != str(shape_id):
            continue
        ctn.set("presetID", "22")
        child = ctn.find(P + "childTnLst")
        if child is None:
            continue
        for eff in child.findall(P + "animEffect"):
            eff.set("transition", "in")
            eff.set("filter", direction)
        for anim in list(child.findall(P + "anim")):
            attr = anim.find(".//" + P + "attrName")
            if attr is not None and (attr.text or "") == "ppt_y":
                child.remove(anim)          # chart frames read better without the rise
        touched += 1
    return touched


def cmd_wipe(args):
    names, data = read(args.pptx)
    part = slide_part(args.slide)
    root = parse(data, part)
    n = wipe_effect(root, args.shape_id, args.direction)
    store(data, part, root)
    write(args.pptx, names, data)
    print("wipe applied to %d effect(s)" % n)


def cmd_media_loop(args):
    names, data = read(args.pptx)
    slides = [args.slide] if args.slide else range(1, 100)
    total = 0
    for s in slides:
        part = slide_part(s)
        if part not in data:
            continue
        root = parse(data, part)
        count = 0
        for vid in root.iter(P + "video"):
            node = vid.find(P + "cMediaNode")
            ctn = node.find(P + "cTn") if node is not None else None
            if ctn is not None:
                ctn.set("repeatCount", "indefinite")
                count += 1
        if count:
            store(data, part, root)
            total += count
            print("slide %d: %d clip(s) set to loop" % (s, count))
    write(args.pptx, names, data)
    print("total looped:", total)


def cmd_recolor(args):
    mapping = {}
    for item in args.map or []:
        old, new = item.split("=")
        mapping[old.upper()] = new.upper()
    names, data = read(args.pptx)
    changed = 0
    for n in names:
        if not re.match(r"ppt/(slides|notesSlides|charts|diagrams)/.+\.xml$", n):
            continue
        if n.startswith("ppt/slides/slide") is False and n.startswith("ppt/charts/") is False:
            continue
        text = data[n].decode("utf-8")
        touched = 0
        for old, new in mapping.items():
            pattern = re.compile(r'(val=")%s(")' % old, re.IGNORECASE)
            text, k = pattern.subn(r"\g<1>%s\g<2>" % new, text)
            touched += k
        if touched:
            data[n] = text.encode("utf-8")
            changed += touched
    write(args.pptx, names, data)
    print("recoloured %d colour node(s)" % changed)


def cmd_replace_media(args):
    assert os.path.exists(args.file), args.file
    names, data = read(args.pptx)
    assert args.part in data, "%s not in package" % args.part
    data[args.part] = open(args.file, "rb").read()
    write(args.pptx, names, data)
    print("replaced %s with %s (%d bytes)" % (args.part, args.file, len(data[args.part])))


def cmd_move(args):
    names, data = read(args.pptx)
    part = slide_part(args.slide)
    root = parse(data, part)
    moved = []
    for el, nv in shapes(root):
        label = nv.get("name") or ""
        text = "".join(t.text or "" for t in el.iter(A + "t")).strip()
        if args.name and not label.startswith(args.name):
            continue
        if args.text and not text.startswith(args.text):
            continue
        xf = el.find(P + "spPr/" + A + "xfrm")
        if xf is None:
            xf = el.find(P + "grpSpPr/" + A + "xfrm")
        if xf is None:
            xf = el.find(P + "xfrm")
        if xf is None:
            continue
        off = xf.find(A + "off")
        if off is None:
            continue
        off.set("x", str(int(off.get("x")) + args.dx))
        off.set("y", str(int(off.get("y")) + args.dy))
        moved.append(label)
    store(data, part, root)
    write(args.pptx, names, data)
    print("moved %d shape(s) on slide %d: %s" % (len(moved), args.slide, moved))
    for label in moved:
        print("  ", label.encode("ascii", "replace").decode())


def cmd_bld_report(args):
    names, data = read(args.pptx)
    for n in names:
        m = re.fullmatch(r"ppt/slides/slide(\d+)\.xml", n)
        if not m:
            continue
        root = parse(data, n)
        rows = []
        for bld in root.iter(P + "bldGraphic"):
            sub = bld.find(P + "bldSub")
            chart = sub.find(A + "bldChart") if sub is not None else None
            rows.append((bld.get("spid"), chart.get("bld") if chart is not None else "asOne"))
        if rows:
            print("slide %-3s %s" % (m.group(1), rows))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("chart-build")
    p.add_argument("pptx")
    p.add_argument("--slide", type=int, required=True)
    p.add_argument("--shape-id", required=True)
    p.add_argument("--mode", default="series",
                   choices=["all", "series", "category", "seriesEl", "categoryEl"])
    p.add_argument("--wipe", help="up|down|left|right (also sets the entrance wipe)")
    p.set_defaults(func=cmd_chart_build)

    p = sub.add_parser("wipe")
    p.add_argument("pptx")
    p.add_argument("--slide", type=int, required=True)
    p.add_argument("--shape-id", required=True)
    p.add_argument("--direction", required=True)
    p.set_defaults(func=cmd_wipe)

    p = sub.add_parser("media-loop")
    p.add_argument("pptx")
    p.add_argument("--slide", type=int)
    p.set_defaults(func=cmd_media_loop)

    p = sub.add_parser("recolor")
    p.add_argument("pptx")
    p.add_argument("--map", action="append", help="OLD=NEW hex pair")
    p.set_defaults(func=cmd_recolor)

    p = sub.add_parser("replace-media")
    p.add_argument("pptx")
    p.add_argument("--part", required=True, help="e.g. ppt/media/media2.mp4")
    p.add_argument("--file", required=True)
    p.set_defaults(func=cmd_replace_media)

    p = sub.add_parser("move")
    p.add_argument("pptx")
    p.add_argument("--slide", type=int, required=True)
    p.add_argument("--name")
    p.add_argument("--text")
    p.add_argument("--dx", type=int, default=0)
    p.add_argument("--dy", type=int, default=0)
    p.set_defaults(func=cmd_move)

    p = sub.add_parser("bld-report")
    p.add_argument("pptx")
    p.set_defaults(func=cmd_bld_report)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
