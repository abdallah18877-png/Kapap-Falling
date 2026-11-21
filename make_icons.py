#!/usr/bin/env python3
"""Generates the KAPAP FALLING launcher icons and writes them into the Capacitor
Android project (android/app/src/main/res). Run after `npx cap add android`.
Usage: python3 make_icons.py [res_dir] [preview.png]"""
import math, os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageChops

RES = sys.argv[1] if len(sys.argv) > 1 else 'android/app/src/main/res'
PREVIEW = sys.argv[2] if len(sys.argv) > 2 else None
BG = (36, 17, 9)

def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))

def vgrad(w, h, top, bot):
    g = Image.new('RGB', (1, h))
    for y in range(h): g.putpixel((0, y), lerp(top, bot, y / max(1, h - 1)))
    return g.resize((w, h))

def chunk(size, cx, cy, ang):
    """one rounded meat chunk, drawn on its own layer"""
    S = size
    L = Image.new('RGBA', (2048, 2048), (0, 0, 0, 0))
    base = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    body = vgrad(S, S, (214, 118, 58), (128, 58, 24)).convert('RGBA')
    m = Image.new('L', (S, S), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * .22), fill=255)
    base.paste(body, (0, 0), m)
    # grill marks (drawn on a separate layer so the skewer never shows through)
    gm = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gm)
    for off in (.28, .56):
        x0 = int(S * off)
        gd.line([(x0, int(S * .08)), (x0 + int(S * .16), int(S * .92))], fill=(58, 24, 10, 210), width=int(S * .07))
    base = Image.alpha_composite(base, gm)
    # soft highlight top-left
    hl = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse([int(S * .1), int(S * .06), int(S * .55), int(S * .36)], fill=(255, 226, 170, 120))
    hl = hl.filter(ImageFilter.GaussianBlur(S * .05))
    base = Image.alpha_composite(base, hl)
    # dark outline
    ol = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(ol).rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * .22), outline=(40, 15, 6, 255), width=int(S * .035))
    base = Image.alpha_composite(base, ol)
    base.putalpha(ImageChops.multiply(base.getchannel('A'), m))
    base = base.rotate(ang, resample=Image.BICUBIC, expand=True)
    L.paste(base, (cx - base.width // 2, cy - base.height // 2), base)
    return L

def kebab():
    """skewer with three chunks, horizontal on 2048 canvas, then tilted"""
    L = Image.new('RGBA', (2048, 2048), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    y = 1024
    # skewer: handle ring + steel rod + pointed tip
    d.rounded_rectangle([190, y - 22, 1840, y + 22], radius=22, fill=(170, 178, 186, 255))
    d.rounded_rectangle([190, y - 22, 1840, y - 6], radius=8, fill=(240, 244, 248, 255))
    d.polygon([(1840, y - 22), (1950, y), (1840, y + 22)], fill=(230, 235, 239, 255))
    d.ellipse([110, y - 60, 250, y + 60], outline=(170, 178, 186, 255), width=24)
    # drop shadow for the rod
    for cx, sz, ang in ((620, 420, 4), (1000, 470, -3), (1400, 430, 5)):
        L = Image.alpha_composite(L, chunk(sz, cx, y, ang))
    L = L.rotate(35, resample=Image.BICUBIC)
    return L

KEB = kebab()
bb = KEB.getchannel('A').getbbox()
KEB = KEB.crop(bb)

def place(canvas, frac, shadow=True):
    """paste the kebab centered, scaled so its longest side = frac * canvas"""
    n = canvas.width
    s = frac * n / max(KEB.size)
    k = KEB.resize((max(1, int(KEB.width * s)), max(1, int(KEB.height * s))), Image.LANCZOS)
    pos = ((n - k.width) // 2, (n - k.height) // 2)
    if shadow:
        sh = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        a = Image.new('RGBA', k.size, (0, 0, 0, 150)); a.putalpha(k.getchannel('A').point(lambda v: int(v * .6)))
        sh.paste(a, (pos[0] + int(n * .012), pos[1] + int(n * .02)), a)
        canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(n * .015)))
    canvas.alpha_composite(k, pos)
    return canvas

def glow(n):
    g = Image.new('RGBA', (n, n), (0, 0, 0, 0))
    px = g.load()
    cx = cy = n / 2
    for y in range(n):
        for x in range(n):
            r = math.hypot(x - cx, y - cy) / (n * .5)
            a = max(0.0, 1 - r) ** 1.6
            px[x, y] = (255, 110, 30, int(190 * a))
    return g

def full_icon(n):
    c = Image.new('RGBA', (n, n), BG + (255,))
    c.alpha_composite(vgrad(n, n, (58, 27, 14), (22, 11, 7)).convert('RGBA'))
    c.alpha_composite(glow(n))
    return place(c, .78)

def foreground(n):
    c = Image.new('RGBA', (n, n), (0, 0, 0, 0))
    c.alpha_composite(glow(n))
    return place(c, .58)   # stays inside the 66/108 adaptive safe zone

MASTER = full_icon(1024)
if PREVIEW: MASTER.convert('RGB').save(PREVIEW)

def rounded(img, r):
    m = Image.new('L', img.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius=int(img.width * r), fill=255)
    o = img.copy(); o.putalpha(m); return o

def circle(img):
    m = Image.new('L', img.size, 0)
    ImageDraw.Draw(m).ellipse([0, 0, img.width - 1, img.height - 1], fill=255)
    o = img.copy(); o.putalpha(m); return o

FG = foreground(1024)
DENS = {'mdpi': 48, 'hdpi': 72, 'xhdpi': 96, 'xxhdpi': 144, 'xxxhdpi': 192}
for name, px in DENS.items():
    d = os.path.join(RES, 'mipmap-' + name)
    os.makedirs(d, exist_ok=True)
    base = MASTER.resize((px, px), Image.LANCZOS)
    rounded(base, .22).save(os.path.join(d, 'ic_launcher.png'))
    circle(base).save(os.path.join(d, 'ic_launcher_round.png'))
    FG.resize((px * 108 // 48, px * 108 // 48), Image.LANCZOS).save(os.path.join(d, 'ic_launcher_foreground.png'))

# make the adaptive-icon definition deterministic
v26 = os.path.join(RES, 'mipmap-anydpi-v26'); os.makedirs(v26, exist_ok=True)
xml = ('<?xml version="1.0" encoding="utf-8"?>\n<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
       '    <background android:drawable="@color/ic_launcher_background"/>\n'
       '    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>\n</adaptive-icon>\n')
for f in ('ic_launcher.xml', 'ic_launcher_round.xml'):
    open(os.path.join(v26, f), 'w').write(xml)
vals = os.path.join(RES, 'values'); os.makedirs(vals, exist_ok=True)
open(os.path.join(vals, 'ic_launcher_background.xml'), 'w').write(
    '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">#241109</color>\n</resources>\n')
print('icons written to', RES)
