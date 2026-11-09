#!/usr/bin/env python
"""Render the identity card for this deck family from assets/identity/brand-tokens.json.

    python make_identity_card.py --tokens assets/identity/brand-tokens.json --out IDENTITY_CARD.png

The card is a one-page visual summary of the house style: palette, type ladder, page
furniture, motifs and the forbidden list. Future decks fork the JSON, re-run this, and get
their own card in the same layout.
"""
import argparse
import json
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 2400, 1560
FONTS = [
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\DejaVuSans.ttf",
]
BOLD = [
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\DejaVuSans-Bold.ttf",
]


def font(size, bold=False):
    for p in (BOLD if bold else FONTS):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def luminance(c):
    def f(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = c
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def dot_screen(w, h, pitch, angle, dot_frac=0.42):
    """Draw a rotated halftone patch with PIL, periodic by construction."""
    img = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(img)
    import math
    t = math.radians(angle)
    span = int((w + h) / pitch) + 4
    r = dot_frac * pitch * 0.5
    for i in range(-span, span):
        for j in range(-span, span):
            u = i * pitch
            v = j * pitch
            x = u * math.cos(t) - v * math.sin(t) + w / 2
            y = u * math.sin(t) + v * math.cos(t) + h / 2
            if -pitch <= x <= w + pitch and -pitch <= y <= h + pitch:
                d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokens", default="assets/identity/brand-tokens.json")
    ap.add_argument("--out", default="IDENTITY_CARD.png")
    ap.add_argument("--title", default=None)
    args = ap.parse_args()
    tok = json.load(open(args.tokens, encoding="utf-8"))

    paper = hex_rgb(tok["palette"]["paper"])
    navy = hex_rgb(tok["palette"]["ink_navy"])
    ice = hex_rgb(tok["palette"]["ink_ice"])
    teal = hex_rgb(tok["palette"]["ink_teal"])
    cap = hex_rgb(tok["palette"]["caption"])

    img = Image.new("RGB", (W, H), paper)
    d = ImageDraw.Draw(img)

    title = args.title or tok.get("identity", "deck identity")
    d.rectangle([0, 0, W, 150], fill=navy)
    d.text((60, 38), title.upper(), font=font(44, True), fill=ice)
    d.text((60, 100), "identity card  ·  palette / type / furniture / motifs",
           font=font(26), fill=(190, 210, 218))

    # ---- palette
    y = 210
    d.text((60, y), "PALETTE (ink on paper)", font=font(30, True), fill=navy)
    y += 56
    order = ["paper", "ink_navy", "ink_teal", "ink_orange", "ink_ice",
             "caption", "grey_strip", "accent_theme2", "data_series_orange"]
    sw_w, sw_h, gap = 236, 150, 18
    for i, key in enumerate(order):
        col = hex_rgb(tok["palette"][key])
        x = 60 + i * (sw_w + gap)
        d.rectangle([x, y, x + sw_w, y + sw_h], fill=col, outline=(0, 0, 0, 40))
        tc = (255, 255, 255) if luminance(col) < 0.42 else (30, 40, 45)
        d.text((x + 10, y + 10), key, font=font(22, True), fill=tc)
        d.text((x + 10, y + sw_h - 40), tok["palette"][key].upper(), font=font(20), fill=tc)
        cr = contrast(col, paper)
        d.text((x + 10, y + sw_h + 8), "on paper %.1f:1" % cr, font=font(18), fill=cap)

    # ---- type ladder
    y = 500
    d.text((60, y), "TYPE LADDER", font=font(30, True), fill=navy)
    y += 54
    scale = tok["type_scale_pt"]
    rows = [("cover_title", "cover title"), ("slide_title", "slide title"),
            ("divider_title", "divider title"), ("list_item", "list item"),
            ("statement", "statement"), ("sidebar_bullet", "side bullet"),
            ("caption", "caption"), ("footer", "footer / page")]
    x1 = 60
    for i, (key, label) in enumerate(rows):
        pt = scale[key]
        size = max(16, int(pt * 1.15))
        yy = y + (i % 4) * 96
        xx = x1 + (i // 4) * 1150
        d.text((xx, yy), "Aa", font=font(size, True), fill=navy)
        d.text((xx + 110, yy + 4), "%s  —  %.1f pt" % (label, pt), font=font(24), fill=cap)

    # ---- page furniture diagram
    y = 940
    d.text((60, y), "PAGE FURNITURE", font=font(30, True), fill=navy)
    y += 52
    gx, gy, gw, gh = 60, y, 980, 470
    d.rectangle([gx, gy, gx + gw, gy + gh], fill=paper, outline=(180, 180, 175), width=2)
    geo = tok["geometry_emu"]
    sy = gh / tok["canvas"]["emu"][1]
    sx = gw / tok["canvas"]["emu"][0]
    band_h = int(geo["header_band"]["height"] * sy)
    rail_h = int(geo["footer_rail"]["height"] * sy)
    d.rectangle([gx, gy, gx + gw, gy + band_h], fill=navy)
    d.rectangle([gx, gy + gh - rail_h, gx + gw, gy + gh], fill=navy)
    d.text((gx + 16, gy + 12), "header band  800000 EMU  ·  ice logos, ice eyebrow",
           font=font(20), fill=ice)
    d.text((gx + 16, gy + gh - rail_h - 30),
           "footer rail  378000 EMU  ·  9.5 pt footer / 12 pt page number, centred",
           font=font(20), fill=cap)
    m = int(geo["margin_x"] * sx)
    d.line([gx + m, gy, gx + m, gy + gh], fill=teal, width=2)
    d.line([gx + gw - m, gy, gx + gw - m, gy + gh], fill=teal, width=2)
    d.text((gx + m + 8, gy + band_h + 16), "margin 609600 EMU both sides",
           font=font(20), fill=cap)
    d.text((gx + m + 8, gy + band_h + 96), "title 31.5 pt bold  +  teal ribbon",
           font=font(26, True), fill=navy)
    d.text((gx + m + 8, gy + band_h + 150), "caption 13.15 pt, contrast >= 6:1",
           font=font(22), fill=cap)

    # ---- motifs
    mx = 1090
    d.text((mx, y - 52), "MOTIFS", font=font(30, True), fill=navy)
    tile = 200
    dots = dot_screen(tile, tile, 14, 35, 0.40)
    navy_img = Image.new("RGB", (tile, tile), navy)
    navy_img.paste(Image.new("RGB", (tile, tile), paper), mask=dots)
    img.paste(navy_img, (mx, y))
    d.text((mx, y + tile + 8), "halftone dots", font=font(22), fill=cap)

    stripes = Image.new("RGB", (tile, tile), paper)
    ds = ImageDraw.Draw(stripes)
    for k in range(-tile, tile * 2, 13):
        ds.line([(k, 0), (k - tile, tile)], fill=teal, width=2)
    img.paste(stripes, (mx + tile + 24, y))
    d.text((mx + tile + 24, y + tile + 8), "single-family stripes", font=font(22), fill=cap)

    tile2 = Image.new("RGB", (tile, tile), navy)
    td = ImageDraw.Draw(tile2)
    for i in range(0, tile, 16):
        for j in range(0, tile, 16):
            td.ellipse([i + 3, j + 3, i + 11, j + 11], fill=paper)
    img.paste(tile2, (mx + 2 * (tile + 24), y))
    d.text((mx + 2 * (tile + 24), y + tile + 8), "pattern tile (dark blocks)",
           font=font(22), fill=cap)

    # ---- rules / forbidden
    y2 = y + tile + 52
    d.text((mx, y2), "RULES", font=font(28, True), fill=navy)
    rules = [
        "one accent + two data inks, nothing else",
        "ice marks on navy, navy text on paper",
        "no white plates behind logos",
        "no extra click stops when enriching motion",
        "no third data colour, no gradient inside bars",
        "no footer/page-number subsets",
    ]
    for i, r in enumerate(rules):
        d.text((mx, y2 + 42 + i * 34), "· " + r, font=font(22), fill=cap)

    d.text((60, H - 54), "fork brand-tokens.json + this card for a new talk; keep the engine files",
           font=font(20), fill=(140, 150, 155))
    img.save(args.out)
    print("wrote", args.out, img.size)


if __name__ == "__main__":
    main()
