# Reads every paving stone of the 4 laying patterns from KANN's sheet "Rechteckpflaster 20 x 10 cm / 10 x 10 cm"
# (the stones are vector rectangles in the PDF) and writes patterns.json, one CSV per pattern and a picture per pattern.
#   pip install pymupdf pillow
#   download https://kann-bausysteme.de/fileadmin/user_upload/kbs_verlegemuster_rechteckpflaster_2020.pdf
#   python extract_patterns.py kbs_verlegemuster_rechteckpflaster_2020.pdf
import csv
import json
import math
import os
import sys

import fitz  # pymupdf
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = "https://kann-bausysteme.de/fileadmin/user_upload/kbs_verlegemuster_rechteckpflaster_2020.pdf"
# Quadrant of the page -> pattern (as printed on the sheet)
PATTERNS = {
    ("left", "top"): dict(key="running_bond", code="BS M011a", name_de="Halbverband", name_en="running bond (half bond)",
                          stones_per_m2={"20x10": 50}),
    ("right", "top"): dict(key="square", code="BS M012a", name_de="Quadrat", name_en="square pattern with 10 x 10 key stones",
                           stones_per_m2={"20x10": 48, "10x10": 4}),
    ("left", "bottom"): dict(key="herringbone", code="BS M013a", name_de="Fischgrät", name_en="herringbone",
                             stones_per_m2={"20x10": 50}),
    ("right", "bottom"): dict(key="parquet", code="BS M014a", name_de="Parkett", name_en="parquet (basket weave)",
                              stones_per_m2={"20x10": 50}),
}


def main(pdf):
    page = fitz.open(pdf)[0]
    stones = []
    for g in page.get_drawings():
        r, fill, line = g["rect"], g.get("fill"), g.get("color")
        w, h = r.width, r.height
        if max(w, h) > 40 or min(w, h) < 15:  # stones only, not the table cells or single lines
            continue
        if g["type"] == "fs" and fill:
            stones.append((r, "white" if min(fill) > 0.99 else "blue"))
        elif g["type"] == "s" and line and max(line) < 0.9:  # outline only (no fill) = white stone
            stones.append((r, "white"))
    unit = max(max(r.width, r.height) for r, _ in stones) / 20.0  # points per cm: long side of a stone = 20 cm
    # Split the page into the 4 samples at the widest empty gap between them (not at the page middle).
    def split(values):
        v = sorted(set(round(x, 1) for x in values))
        gap, at = max((b - a, (a + b) / 2) for a, b in zip(v, v[1:]))
        return at
    x_cut = split([e for r, _ in stones for e in (r.x0, r.x1)])
    y_cut = split([e for r, _ in stones for e in (r.y0, r.y1)])
    print(f"{len(stones)} stones, {unit:.4f} pt per cm, split at x={x_cut:.0f} y={y_cut:.0f} pt")

    out = {"source": SOURCE, "units": "cm", "axes": "x to the right, y up, origin = bottom-left corner of the sample",
           "rotation": "0 = long side along x, 90 = long side along y", "patterns": []}
    for (sx, sy), meta in PATTERNS.items():
        mine = [(r, c) for r, c in stones
                if ((r.x0 + r.x1) / 2 < x_cut) == (sx == "left") and ((r.y0 + r.y1) / 2 < y_cut) == (sy == "top")]
        x0 = min(r.x0 for r, _ in mine)
        y1 = max(r.y1 for r, _ in mine)
        rows = []
        for r, c in mine:
            w, h = round(r.width / unit), round(r.height / unit)
            cx, cy = ((r.x0 + r.x1) / 2 - x0) / unit, (y1 - (r.y0 + r.y1) / 2) / unit
            size = "10x10" if w == h else "20x10"
            rows.append(dict(x=round(cx, 1), y=round(cy, 1), size=size, rotation=0 if w >= h else 90,
                             white_on_sheet=(c == "white")))
        rows.sort(key=lambda s: (round(s["y"] - (5 if s["rotation"] == 90 else 0)), s["x"]))  # bottom row first, left to right
        for i, s in enumerate(rows, 1):
            s["id"] = i
        sample = (round((max(r.x1 for r, _ in mine) - x0) / unit), round((y1 - min(r.y0 for r, _ in mine)) / unit))
        pat = dict(meta, sample_cm=list(sample), stone_count=len(rows), repeat_cm=repeat_vectors(rows, sample),
                   stones=[{k: s[k] for k in ("id", "x", "y", "size", "rotation", "white_on_sheet")} for s in rows])
        out["patterns"].append(pat)
        with open(os.path.join(HERE, f"{meta['key']}.csv"), "w", newline="", encoding="utf-8") as f:
            wr = csv.DictWriter(f, fieldnames=["id", "x", "y", "size", "rotation", "white_on_sheet"])
            wr.writeheader()
            wr.writerows(pat["stones"])
        draw_pattern(pat)
        print(f"{meta['code']} {meta['name_de']}: {len(rows)} stones, sample {sample[0]} x {sample[1]} cm")
    with open(os.path.join(HERE, "patterns.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)


def repeat_vectors(rows, sample):
    """The two shortest shifts that map the pattern onto itself: copy every stone by
    i * v1 + j * v2 to cover any area with the same pattern."""
    W, H = sample
    S = {(s["x"], s["y"], s["size"], s["rotation"]) for s in rows}

    def fits(t):
        hit = tot = 0
        for x, y, size, rot in S:
            nx, ny = round(x + t[0], 1), round(y + t[1], 1)
            if 12 <= nx <= W - 12 and 12 <= ny <= H - 12:  # only check targets well inside the sample
                tot += 1
                hit += (nx, ny, size, rot) in S
        return tot > 8 and hit == tot

    cands = {(round(b[0] - a[0], 1), round(b[1] - a[1], 1)) for a in S for b in S if a[2:] == b[2:] and a != b}
    cands = sorted((t for t in cands if t[1] > 0 or (t[1] == 0 and t[0] > 0)), key=lambda t: (math.hypot(*t), -t[1]))
    good = [t for t in cands if fits(t)]
    v1 = good[0]
    v2 = next(t for t in good if abs(v1[0] * t[1] - v1[1] * t[0]) > 1e-6)
    return [list(v1), list(v2)]


def draw_pattern(pat, px=6, pad=30):
    """Our own drawing of a pattern from the extracted data, with stone ids (1 cm = px pixels)."""
    sw, sh = pat["sample_cm"]
    img = Image.new("RGB", (sw * px + 2 * pad, sh * px + 2 * pad + 30), "white")
    d = ImageDraw.Draw(img)
    try:
        font, title = ImageFont.truetype("arial.ttf", 13), ImageFont.truetype("arial.ttf", 18)
    except OSError:
        font = title = ImageFont.load_default()
    d.text((pad, 8), f"{pat['code']} {pat['name_de']} ({pat['name_en']})", fill="black", font=title)
    for s in pat["stones"]:
        L, S = (20, 10) if s["size"] == "20x10" else (10, 10)
        w, h = (L, S) if s["rotation"] == 0 else (S, L)
        x0 = pad + (s["x"] - w / 2) * px
        y0 = 30 + pad + (sh - s["y"] - h / 2) * px
        colour = "#f2f2f2" if s["white_on_sheet"] else ("#f4c27a" if s["size"] == "10x10" else "#c9d7ea")
        d.rectangle([x0, y0, x0 + w * px, y0 + h * px], fill=colour, outline="#333333", width=2)
        d.text((x0 + w * px / 2, y0 + h * px / 2), str(s["id"]), fill="black", font=font, anchor="mm")
    d.text((pad, img.height - pad + 6), "0,0", fill="#888888", font=font)
    img.save(os.path.join(HERE, f"{pat['key']}.png"))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "kbs_verlegemuster_rechteckpflaster_2020.pdf")
