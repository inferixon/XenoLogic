from pathlib import Path

import imageio
from PIL import Image


SOURCE_PATH = Path(__file__).with_name("whitenoise.mp4")
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "Assets"
WEBP_PATH = OUTPUT_DIR / "whitenoise.webp"
GIF_PATH = OUTPUT_DIR / "whitenoise.gif"
FRAME_COUNT = 12
TARGET_SIZE = (1280, 720)
FRAME_DURATION_MS = 80


def sample_frame_indices(total_frames: int, wanted_frames: int) -> list[int]:
    if total_frames <= wanted_frames:
        return list(range(total_frames))

    step = (total_frames - 1) / (wanted_frames - 1)
    return sorted({round(index * step) for index in range(wanted_frames)})


def build_animation_frames() -> list[Image.Image]:
    reader = imageio.get_reader(str(SOURCE_PATH))
    metadata = reader.get_meta_data()
    fps = float(metadata.get("fps") or 30)
    duration_seconds = float(metadata.get("duration") or 0)
    total_frames = max(1, round(duration_seconds * fps))
    frame_indices = sample_frame_indices(total_frames, FRAME_COUNT)

    frames: list[Image.Image] = []

    try:
        for frame_index in frame_indices:
            frame = reader.get_data(frame_index)
            image = Image.fromarray(frame).convert("RGB")
            frames.append(image.resize(TARGET_SIZE, Image.Resampling.BICUBIC))
    finally:
        reader.close()

    return frames


def save_assets(frames: list[Image.Image]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    first_frame, *rest_frames = frames

    first_frame.save(
        WEBP_PATH,
        format="WEBP",
        save_all=True,
        append_images=rest_frames,
        duration=FRAME_DURATION_MS,
        loop=0,
        lossless=False,
        quality=70,
        method=6,
    )

    palette_frames = [
        frame.convert("P", palette=Image.Palette.ADAPTIVE, colors=64) for frame in frames
    ]
    first_palette, *rest_palette = palette_frames

    first_palette.save(
        GIF_PATH,
        format="GIF",
        save_all=True,
        append_images=rest_palette,
        duration=FRAME_DURATION_MS,
        loop=0,
        optimize=True,
        disposal=2,
    )


def main() -> None:
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(f"Missing source video: {SOURCE_PATH}")

    frames = build_animation_frames()
    if not frames:
        raise RuntimeError("No frames extracted from source video.")

    save_assets(frames)

    print(f"Created: {WEBP_PATH}")
    print(f"Created: {GIF_PATH}")


if __name__ == "__main__":
    main()