#!/usr/bin/env python
"""ComfyUI texture pipeline: generate -> post-process into deck-ready ink-on-paper assets.

Wraps the local ComfyUI CLI (E:\\ComfyUI\\draw.cmd) with prompt presets and the
screen-print post-processing this deck family uses, and writes a reproduction receipt.

Examples
    python gen_texture.py --preset halftone-paper --count 2 --out assets\\v41 --bake
    python gen_texture.py --preset stripe-field --count 1 --out assets\\v41 --tone 087F8C
    python gen_texture.py --preset paper-grain --out assets\\v41 --width 1920 --height 1080
    python gen_texture.py --list-presets

Every run writes <out>\\RECEIPT_gen_texture_<stamp>.json with prompt, size, seed, tool,
post-processing and sha256 of the produced files.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageFilter

COMFY_HOME = os.environ.get("COMFYUI", "")
COMFY = os.path.join(COMFY_HOME, "draw.cmd") if COMFY_HOME else ""
COMFY_OUT = os.path.join(COMFY_HOME, "output", "draw") if COMFY_HOME else ""

PALETTE = {
    "paper": "#FBF6EE",
    "ink_navy": "#17364A",
    "ink_teal": "#087F8C",
    "ink_orange": "#CB672A",
    "ink_ice": "#DDEBEF",
    "plate": "#FDFDFC",
}

PRESETS = {
    "halftone-paper": {
        "prompt": ("screen printed halftone dot texture, single ink colour on warm off-white "
                   "paper, coarse regular dot grid, printmaking, no text, no logo, flat, "
                   "high contrast, seamless"),
        "size": (1024, 576),
        "bake": "halftone",
    },
    "stripe-field": {
        "prompt": ("fine diagonal line screen, one direction only, thin parallel lines, ink on "
                   "warm paper, technical print, no text, flat, seamless"),
        "size": (1024, 576),
        "bake": "stripe",
    },
    "paper-grain": {
        "prompt": ("blank warm off-white paper texture, subtle fibre grain, faint mottling, "
                   "no shadows, no objects, no text, even lighting, seamless"),
        "size": (1024, 576),
        "bake": "grain",
    },
    "road-concept": {
        "prompt": ("top down view of a stylised two lane road, flat screen printed colours, "
                   "teal verge, slate asphalt, dashed centre line, no cars, no text"),
        "size": (1024, 576),
        "bake": "crop",
    },
    "block-panel": {
        "prompt": ("solid deep navy panel with sparse pale dots, screen print texture, flat, "
                   "no text, no gradient"),
        "size": (1024, 576),
        "bake": "crop",
    },
}


def hex_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def resolve_color(name):
    return hex_rgb(PALETTE.get(name, name))


# ------------------------------------------------------------------ generate
def run_comfy(prompt, width, height, count, seed, lcm, out_dir, ckpt=None, steps=None, cfg=None):
    if not COMFY or not os.path.exists(COMFY):
        raise SystemExit("ComfyUI not configured: set COMFYUI=<comfy home> or run scripts/detect_tools.py")
    os.makedirs(out_dir, exist_ok=True)
    before = set(os.listdir(COMFY_OUT)) if os.path.isdir(COMFY_OUT) else set()
    cmd = [COMFY, prompt, "-Width", str(width), "-Height", str(height),
           "-Count", str(count), "-OutDir", out_dir]
    if seed is not None:
        cmd += ["-Seed", str(seed)]
    if lcm:
        cmd += ["-Lcm"]
    if steps:
        cmd += ["-Steps", str(steps)]
    if cfg:
        cmd += ["-Cfg", str(cfg)]
    if ckpt:
        cmd += ["-Ckpt", ckpt]
    print("[comfy]", " ".join(cmd[:1] + ["<prompt>"] + cmd[2:]))
    t0 = time.time()
    proc = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace", timeout=900)
    took = time.time() - t0
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout[-2000:] + "\n" + proc.stderr[-2000:] + "\n")
        raise SystemExit("ComfyUI failed (%d)" % proc.returncode)
    files = [os.path.join(out_dir, f) for f in sorted(os.listdir(out_dir))
             if f.lower().endswith(".png")]
    after = set(os.listdir(COMFY_OUT)) - before if os.path.isdir(COMFY_OUT) else set()
    new_from_cache = [os.path.join(COMFY_OUT, f) for f in sorted(after)]
    produced = [f for f in files] + new_from_cache
    produced = [f for f in produced if os.path.getmtime(f) >= t0 - 5]
    if not produced:
        raise SystemExit("ComfyUI ran but produced no new PNG (see %s)" % COMFY_OUT)
    return produced, took


# ------------------------------------------------------------ post-process
def dot_screen(w, h, pitch=14, angle=35.0, dot_frac=0.42, aa=0.8):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    t = np.deg2rad(angle)
    c, s = np.cos(t), np.sin(t)
    u = xx * c + yy * s
    v = -xx * s + yy * c
    cu = (u / pitch) % 1.0 - 0.5
    cv = (v / pitch) % 1.0 - 0.5
    r = np.sqrt(cu * cu + cv * cv)
    edge = dot_frac * 0.7071
    return 1.0 / (1.0 + np.exp(-(r - edge) / (aa / pitch)))


def bake_halftone(src, size, ink, paper, pitch, angle, keep_clear=None, blur=0.0):
    img = Image.open(src).convert("L")
    if blur > 0:
        img = img.filter(ImageFilter.GaussianBlur(blur))   # avoid double-screening AI dots
    img = img.resize(size, Image.LANCZOS)
    tone = np.asarray(img, np.float32) / 255.0
    lo, hi = np.percentile(tone, 5), np.percentile(tone, 95)
    tone = np.clip((tone - lo) / max(1e-6, hi - lo), 0, 1)       # stretch to full range
    w, h = size
    screen = dot_screen(w, h, pitch=pitch, angle=angle)
    coverage = 0.18 + 0.72 * (1.0 - tone)                        # paper never fully clean
    alpha = np.clip(screen * coverage, 0, 1) * 0.92
    if keep_clear:
        mask = Image.new("L", size, 0)
        from PIL import ImageDraw
        ImageDraw.Draw(mask).rectangle(keep_clear, fill=255)
        m = np.asarray(mask.filter(ImageFilter.GaussianBlur(pitch * 4)), np.float32) / 255.0
        alpha *= (1.0 - m)
    out = paper[None, None, :] * (1 - alpha[..., None]) + ink[None, None, :] * alpha[..., None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


def bake_stripe(src, size, ink, paper, pitch, angle, blur=0.0):
    img = Image.open(src).convert("L")
    if blur > 0:
        img = img.filter(ImageFilter.GaussianBlur(blur))
    img = img.resize(size, Image.LANCZOS)
    tone = np.asarray(img, np.float32) / 255.0
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u = xx * np.cos(np.deg2rad(angle)) + yy * np.sin(np.deg2rad(angle))
    band = ((u % pitch) < max(1.0, pitch * 0.18)).astype(np.float32)
    alpha = band * (0.85 - 0.55 * tone)
    out = paper[None, None, :] * (1 - alpha[..., None]) + ink[None, None, :] * alpha[..., None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


def bake_grain(src, size, paper, amp=6.0):
    img = Image.open(src).convert("L").resize(size, Image.LANCZOS)
    n = (np.asarray(img, np.float32) - 128.0) / 255.0 * amp
    base = np.broadcast_to(paper, (size[1], size[0], 3)).astype(np.float32).copy()
    return Image.fromarray(np.clip(base + n[..., None], 0, 255).astype(np.uint8), "RGB")


def crop_resize(src, size):
    img = Image.open(src).convert("RGB")
    w, h = size
    scale = max(w / img.width, h / img.height)
    img = img.resize((max(w, int(img.width * scale)), max(h, int(img.height * scale))), Image.LANCZOS)
    left = (img.width - w) // 2
    top = (img.height - h) // 2
    return img.crop((left, top, left + w, top + h))


def seam_check(img, tol=3.0):
    a = np.asarray(img, np.int16)
    return {
        "vertical": float(np.abs(a[:, 0] - a[:, -1]).mean()),
        "horizontal": float(np.abs(a[0, :] - a[-1, :]).mean()),
        "ok": bool(np.abs(a[:, 0] - a[:, -1]).mean() < tol and np.abs(a[0, :] - a[-1, :]).mean() < tol),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preset", choices=sorted(PRESETS))
    ap.add_argument("--list-presets", action="store_true")
    ap.add_argument("--out", default="assets/textures")
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--width", type=int, default=0)
    ap.add_argument("--height", type=int, default=0)
    ap.add_argument("--size", default="1920x1080", help="final size, WxH")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--lcm", action="store_true")
    ap.add_argument("--steps", type=int, default=None)
    ap.add_argument("--cfg", type=float, default=None)
    ap.add_argument("--ckpt", default=None)
    ap.add_argument("--bake", dest="bake", default=None,
                    choices=["halftone", "stripe", "grain", "crop"], help="override preset post-process")
    ap.add_argument("--ink", default="ink_navy")
    ap.add_argument("--paper", default="paper")
    ap.add_argument("--pitch", type=float, default=14.0)
    ap.add_argument("--blur", type=float, default=0.0,
                    help="pre-blur the AI image before screening (2-4 avoids double dots)")
    ap.add_argument("--angle", type=float, default=35.0)
    ap.add_argument("--keep-clear", default=None, help="x0,y0,x1,y1 in final pixels")
    ap.add_argument("--jpeg-quality", type=int, default=92)
    ap.add_argument("--raw-only", action="store_true")
    ap.add_argument("--from-raw", default=None,
                    help="re-bake these PNG(s), comma separated, instead of calling ComfyUI")
    args = ap.parse_args()

    if args.list_presets or not args.preset:
        for k, v in PRESETS.items():
            print("%-16s %s" % (k, v["prompt"][:90]))
        return

    preset = PRESETS[args.preset]
    size = tuple(int(v) for v in args.size.lower().split("x"))
    gen_w = args.width or preset["size"][0]
    gen_h = args.height or preset["size"][1]
    os.makedirs(args.out, exist_ok=True)

    if args.from_raw:
        produced = [p.strip() for p in args.from_raw.split(",") if p.strip()]
        took = 0.0
        print("[raw] re-baking %d existing image(s)" % len(produced))
    else:
        produced, took = run_comfy(preset["prompt"], gen_w, gen_h, args.count, args.seed,
                                   args.lcm, args.out, args.ckpt, args.steps, args.cfg)
        print("[comfy] %d image(s) in %.1f s" % (len(produced), took))

    ink = resolve_color(args.ink)
    paper = resolve_color(args.paper)
    keep = None
    if args.keep_clear:
        keep = tuple(int(v) for v in args.keep_clear.split(","))
    mode = args.bake or preset["bake"]

    outputs = []
    for i, src in enumerate(produced):
        if args.raw_only:
            dst = os.path.join(args.out, "%s_%02d_raw.png" % (args.preset, i + 1))
            Image.open(src).convert("RGB").save(dst)
        else:
            if mode == "halftone":
                img = bake_halftone(src, size, ink, paper, args.pitch, args.angle, keep, args.blur)
            elif mode == "stripe":
                img = bake_stripe(src, size, ink, paper, args.pitch, args.angle, args.blur)
            elif mode == "grain":
                img = bake_grain(src, size, paper)
            else:
                img = crop_resize(src, size)
            dst = os.path.join(args.out, "%s_%02d.jpg" % (args.preset, i + 1))
            img.save(dst, quality=args.jpeg_quality, subsampling=1)
            info = seam_check(img) if mode in ("halftone", "stripe") else None
            outputs.append({"file": dst, "mode": mode, "sha256": sha(dst),
                            "size": list(img.size), "edge_mismatch": info})

    receipt = {
        "generator": "gen_texture.py",
        "comfy_cmd": COMFY,
        "preset": args.preset,
        "prompt": preset["prompt"],
        "generated_size": [gen_w, gen_h],
        "count": args.count,
        "seed": args.seed,
        "lcm": args.lcm,
        "ckpt": args.ckpt,
        "took_seconds": round(took, 1),
        "post_process": {"mode": mode, "ink": args.ink, "paper": args.paper,
                         "pitch": args.pitch, "angle": args.angle,
                         "final_size": list(size), "jpeg_quality": args.jpeg_quality},
        "outputs": outputs,
        "raw_sources": produced,
        "made_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    stamp = time.strftime("%Y%m%d_%H%M%S")
    rp = os.path.join(args.out, "RECEIPT_gen_texture_%s.json" % stamp)
    with open(rp, "w", encoding="utf-8") as f:
        json.dump(receipt, f, ensure_ascii=False, indent=2)
    print("[done]", len(outputs), "asset(s) +", rp)
    for o in outputs:
        print("  ", o["file"], "| edges continuous" if not o["edge_mismatch"] or o["edge_mismatch"]["ok"] else "| note: edges differ (fine unless tiled) %s" % o["edge_mismatch"])


if __name__ == "__main__":
    main()
