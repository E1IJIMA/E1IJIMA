#!/usr/bin/env python3
"""Create the animated anime showcase GIF for the profile README.

Run from the repository root:
    python scripts/create_anime_gif.py

The script reads the four source PNGs in anime/ and writes
assets/anime-showcase.gif. Source PNGs are never modified.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "anime"
OUTPUT = ROOT / "assets" / "anime-showcase.gif"
SOURCE_FILES = [SOURCE_DIR / f"anime-girl-{index}.png" for index in range(1, 5)]

CANVAS = (420, 420)
BACKGROUND = (255, 245, 250, 255)  # #FFF5FA
HOLD_MS = 1500
FADE_MS = 300
FADE_STEP_MS = 100
LOOP_DELAY_MS = 2000


def prepare_frame(image: Image.Image) -> Image.Image:
    """Fit an image into the square canvas without changing its aspect ratio."""
    image = image.convert("RGBA")
    image.thumbnail(CANVAS, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", CANVAS, BACKGROUND)
    x = (CANVAS[0] - image.width) // 2
    y = (CANVAS[1] - image.height) // 2
    canvas.alpha_composite(image, (x, y))
    return canvas


def quantize(frame: Image.Image) -> Image.Image:
    """Reduce color count for a smaller GitHub-friendly GIF while keeping quality."""
    rgb = frame.convert("RGB")
    return rgb.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)


def build_frames() -> tuple[list[Image.Image], list[int]]:
    sources = [prepare_frame(Image.open(path)) for path in SOURCE_FILES]
    frames: list[Image.Image] = []
    durations: list[int] = []

    # 1 → 2 → 3 → 4 → 1, with a short crossfade at every boundary.
    for index, current in enumerate(sources):
        next_frame = sources[(index + 1) % len(sources)]
        frames.append(current.copy())
        durations.append(HOLD_MS)

        for step in range(1, FADE_MS // FADE_STEP_MS + 1):
            alpha = step / (FADE_MS // FADE_STEP_MS + 1)
            blended = Image.blend(current, next_frame, alpha)
            frames.append(blended)
            durations.append(FADE_STEP_MS)

    # Make the start frame linger slightly at the end of the loop for a calm reset.
    durations[-1] += LOOP_DELAY_MS
    return frames, durations


def main() -> None:
    missing = [path for path in SOURCE_FILES if not path.is_file()]
    if missing:
        names = ", ".join(str(path.relative_to(ROOT)) for path in missing)
        raise FileNotFoundError(f"Missing source image(s): {names}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frames, durations = build_frames()
    quantized = [quantize(frame) for frame in frames]

    quantized[0].save(
        OUTPUT,
        save_all=True,
        append_images=quantized[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )

    print(f"Created {OUTPUT.relative_to(ROOT)} ({OUTPUT.stat().st_size:,} bytes)")
    print("Sequence: 1 → 2 → 3 → 4 → 1")
    print(f"Frames: {len(quantized)} | canvas: {CANVAS[0]}×{CANVAS[1]} px")


if __name__ == "__main__":
    main()
