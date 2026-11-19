"""Draw the app icons (public/*.png, public/favicon.svg): a gold spade on green felt.

    python scripts/make-icons.py

Uses the spade path from src/ui/cards/cardArt.ts (a 100 x 100 box).
"""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

SPADE = "M50 3C62 22 96 39 96 62C96 77 85 85 73 85C64 85 57 80 53 73C54 84 58 92 67 98H33C42 92 46 84 47 73C43 80 36 85 27 85C15 85 4 77 4 62C4 39 38 22 50 3Z"
OUT = Path(__file__).resolve().parent.parent / "public"


def path_points(d: str, steps: int = 24) -> list[tuple[float, float]]:
    tokens = re.findall(r"[MCHZ]|-?\d+(?:\.\d+)?", d)
    pts: list[tuple[float, float]] = []
    i = 0
    cur = (0.0, 0.0)
    while i < len(tokens):
        t = tokens[i]
        i += 1
        if t == "M":
            cur = (float(tokens[i]), float(tokens[i + 1]))
            i += 2
            pts.append(cur)
        elif t == "C":
            while i < len(tokens) and tokens[i] not in "MCHZ":
                p1 = (float(tokens[i]), float(tokens[i + 1]))
                p2 = (float(tokens[i + 2]), float(tokens[i + 3]))
                p3 = (float(tokens[i + 4]), float(tokens[i + 5]))
                i += 6
                for k in range(1, steps + 1):
                    s = k / steps
                    x = (1 - s) ** 3 * cur[0] + 3 * (1 - s) ** 2 * s * p1[0] + 3 * (1 - s) * s * s * p2[0] + s**3 * p3[0]
                    y = (1 - s) ** 3 * cur[1] + 3 * (1 - s) ** 2 * s * p1[1] + 3 * (1 - s) * s * s * p2[1] + s**3 * p3[1]
                    pts.append((x, y))
                cur = p3
        elif t == "H":
            cur = (float(tokens[i]), cur[1])
            i += 1
            pts.append(cur)
        elif t == "Z":
            pass
    return pts


def icon(size: int, maskable: bool = False) -> Image.Image:
    scale = 4  # supersample
    s = size * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    # Felt: radial-ish gradient in a rounded square (full bleed when maskable).
    bg = Image.new("RGBA", (s, s))
    px = bg.load()
    for y in range(s):
        for x in range(s):
            dx, dy = (x - s * 0.5) / s, (y - s * 0.42) / s
            t = min(1.0, (dx * dx + dy * dy) ** 0.5 * 1.6)
            r = int(35 + (11 - 35) * t)
            g = int(117 + (52 - 117) * t)
            b = int(86 + (38 - 86) * t)
            px[x, y] = (r, g, b, 255)
    mask = Image.new("L", (s, s), 0)
    radius = 0 if maskable else int(s * 0.22)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, s - 1, s - 1), radius=radius, fill=255)
    img.paste(bg, (0, 0), mask)
    draw = ImageDraw.Draw(img)
    if not maskable:
        inset = int(s * 0.045)
        draw.rounded_rectangle((inset, inset, s - 1 - inset, s - 1 - inset), radius=int(s * 0.18), outline=(233, 196, 106, 120), width=max(2, int(s * 0.012)))
    # The spade, with a soft shadow.
    box = s * (0.5 if maskable else 0.6)
    ox, oy = (s - box) / 2, (s - box) / 2 + s * 0.01
    pts = [(ox + x / 100 * box, oy + y / 100 * box) for x, y in path_points(SPADE)]
    shadow = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).polygon([(x, y + s * 0.025) for x, y in pts], fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(s * 0.02))
    img.alpha_composite(shadow)
    gold = Image.new("RGBA", (s, s))
    gp = gold.load()
    for y in range(s):
        t = y / s
        c = (int(255 - 60 * t), int(240 - 85 * t), int(190 - 140 * t), 255)
        for x in range(s):
            gp[x, y] = c
    smask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(smask).polygon(pts, fill=255)
    img.paste(gold, (0, 0), smask)
    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    icon(192).save(OUT / "icon-192.png")
    icon(512).save(OUT / "icon-512.png")
    icon(512, maskable=True).save(OUT / "icon-maskable-512.png")
    icon(180, maskable=True).convert("RGB").save(OUT / "apple-touch-icon.png")
    (OUT / "favicon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<defs><radialGradient id="f" cx=".5" cy=".42" r=".7"><stop offset="0" stop-color="#237556"/><stop offset="1" stop-color="#0b3426"/></radialGradient>'
        '<linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff0be"/><stop offset="1" stop-color="#c4932f"/></linearGradient></defs>'
        '<rect width="100" height="100" rx="22" fill="url(#f)"/>'
        f'<path transform="translate(20 21) scale(.6)" d="{SPADE}" fill="url(#g)"/></svg>',
        encoding="utf8",
    )
    print("icons written to", OUT)


if __name__ == "__main__":
    main()
