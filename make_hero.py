#!/usr/bin/env python3
"""Build assets/hero.gif - the animated slideshow at the top of the profile README.

Reads the four scene stills from assets/scenes/, holds each one for a beat,
cross-fades into the next, and writes a looping GIF with a shared palette
(so colours don't flicker between frames).

Usage:  python3 assets/make_hero.py
Requires: Pillow  (pip install pillow)
"""

from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent
SCENES = ROOT / "scenes"
OUT = ROOT / "hero.gif"

WIDTH, HEIGHT = 900, 383       # ~2.35:1, matches the source art
HOLD_MS = 2600                 # how long each scene sits still
FADE_FRAMES = 8                # frames spent cross-fading
FADE_FRAME_MS = 65             # -> ~0.5s cross-fade
SOFTEN = 0.5                   # slight blur: smoother gradients, smaller GIF

SCENE_FILES = [
    "01-kolkata.jpg",
    "02-satellite.jpg",
    "03-farmland.jpg",
    "04-desk.jpg",
]


def load_scene(path: Path) -> Image.Image:
    """Centre-crop to the target aspect ratio, then resize."""
    img = Image.open(path).convert("RGB")
    src_ratio = img.width / img.height
    dst_ratio = WIDTH / HEIGHT
    if src_ratio > dst_ratio:
        new_w = int(img.height * dst_ratio)
        left = (img.width - new_w) // 2
        img = img.crop((left, 0, left + new_w, img.height))
    else:
        new_h = int(img.width / dst_ratio)
        top = (img.height - new_h) // 2
        img = img.crop((0, top, img.width, top + new_h))
    img = img.resize((WIDTH, HEIGHT), Image.LANCZOS)
    return img.filter(ImageFilter.GaussianBlur(SOFTEN)) if SOFTEN else img


def shared_palette(scenes):
    """One 256-colour palette sampled from all scenes -> no colour flicker."""
    strip = Image.new("RGB", (256 * len(scenes), 256))
    for i, scene in enumerate(scenes):
        strip.paste(scene.resize((256, 256), Image.LANCZOS), (i * 256, 0))
    return strip.quantize(colors=256, method=Image.MEDIANCUT)


def build_frames(scenes):
    frames, durations = [], []

    def add(img, ms):
        frames.append(img.quantize(palette=palette, dither=Image.NONE))
        durations.append(ms)

    for i, scene in enumerate(scenes):
        nxt = scenes[(i + 1) % len(scenes)]
        add(scene, HOLD_MS)
        for step in range(1, FADE_FRAMES + 1):
            add(Image.blend(scene, nxt, step / (FADE_FRAMES + 1)), FADE_FRAME_MS)

    return frames, durations


if __name__ == "__main__":
    scenes = [load_scene(SCENES / name) for name in SCENE_FILES]
    palette = shared_palette(scenes)
    frames, durations = build_frames(scenes)

    frames[0].save(
        OUT,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=1,
    )
    print(f"wrote {OUT} - {OUT.stat().st_size / 1e6:.2f} MB, {len(frames)} frames")
