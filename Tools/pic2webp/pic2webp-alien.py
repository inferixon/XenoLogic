from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from shutil import which


SCRIPT_DIR = Path(__file__).resolve().parent
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}
STATIC_EXTENSIONS = {".jpg", ".jpeg", ".png"}
STATIC_QUALITY = "90"
ANIMATED_QUALITY = "88"
COMPRESSION_LEVEL = "6"
TARGET_WIDTH = 208
TARGET_HEIGHT = 248
OUTPUT_PREFIX = "alien-"


def resolve_binary_path(binary_name: str) -> Path | None:
    candidate_paths = [
        SCRIPT_DIR / binary_name,
        SCRIPT_DIR.parent / "ffmpeg" / binary_name,
    ]

    for parent in SCRIPT_DIR.parents:
        candidate_paths.append(parent / "TOOLS" / "ffmpeg" / binary_name)

    for candidate in candidate_paths:
        if candidate.exists():
            return candidate

    binary_from_path = which(Path(binary_name).stem)
    if binary_from_path:
        return Path(binary_from_path)

    return None


FFMPEG_PATH = resolve_binary_path("ffmpeg.exe")
FFPROBE_PATH = resolve_binary_path("ffprobe.exe")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert images to exact 208x248 WebP by stretching them with no padding."
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Files or directories to convert. Defaults to the script folder.",
    )
    parser.add_argument(
        "--keep-originals",
        action="store_true",
        help="Keep source files after successful conversion.",
    )
    return parser.parse_args()


def iter_supported_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix.lower() in SUPPORTED_EXTENSIONS else []

    if path.is_dir():
        return [
            child
            for child in sorted(path.iterdir())
            if child.is_file() and child.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

    return []


def get_source_files(inputs: list[str]) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    raw_inputs = inputs or [str(SCRIPT_DIR)]

    for raw_input in raw_inputs:
        source_path = Path(raw_input).expanduser().resolve()

        for path in iter_supported_files(source_path):
            if path in seen:
                continue

            seen.add(path)
            files.append(path)

    return files


def build_resize_filter() -> str:
    return f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}"


def build_common_filter_args() -> list[str]:
    return ["-vf", build_resize_filter()]


def build_command(source_file: Path, target_file: Path) -> list[str]:
    if FFMPEG_PATH is None:
        raise RuntimeError("ffmpeg executable was not found")

    suffix = source_file.suffix.lower()

    if suffix == ".gif":
        return [
            str(FFMPEG_PATH),
            "-y",
            "-i",
            str(source_file),
            "-map",
            "0:v:0",
            *build_common_filter_args(),
            "-c:v",
            "libwebp_anim",
            "-quality",
            ANIMATED_QUALITY,
            "-compression_level",
            COMPRESSION_LEVEL,
            "-loop",
            "0",
            "-an",
            str(target_file),
        ]

    if suffix in STATIC_EXTENSIONS:
        return [
            str(FFMPEG_PATH),
            "-y",
            "-i",
            str(source_file),
            "-map",
            "0:v:0",
            *build_common_filter_args(),
            "-c:v",
            "libwebp",
            "-quality",
            STATIC_QUALITY,
            "-compression_level",
            COMPRESSION_LEVEL,
            "-pix_fmt",
            "yuva420p",
            str(target_file),
        ]

    raise ValueError(f"Unsupported input format: {source_file}")


def get_output_dimensions(target_file: Path) -> tuple[int, int]:
    if FFPROBE_PATH is None:
        raise RuntimeError("ffprobe executable was not found")

    probe_command = [
        str(FFPROBE_PATH),
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=p=0:s=x",
        str(target_file),
    ]
    completed = subprocess.run(probe_command, capture_output=True, text=True)

    if completed.returncode != 0:
        error_output = completed.stderr.strip() or completed.stdout.strip() or "Unknown ffprobe error"
        raise RuntimeError(f"Dimension check failed for {target_file.name}: {error_output}")

    dimensions = completed.stdout.strip()
    width_text, height_text = dimensions.split("x", maxsplit=1)
    return int(width_text), int(height_text)


def convert_file(source_file: Path, keep_originals: bool) -> None:
    target_file = source_file.with_name(f"{OUTPUT_PREFIX}{source_file.stem}.webp")
    command = build_command(source_file, target_file)

    print(f"Converting {source_file.name} -> {target_file.name}")
    completed = subprocess.run(command, capture_output=True, text=True)

    if completed.returncode != 0:
        error_output = completed.stderr.strip() or completed.stdout.strip() or "Unknown ffmpeg error"
        raise RuntimeError(f"Conversion failed for {source_file.name}: {error_output}")

    width, height = get_output_dimensions(target_file)
    if width != TARGET_WIDTH or height != TARGET_HEIGHT:
        target_file.unlink(missing_ok=True)
        raise RuntimeError(
            f"Wrong output size for {target_file.name}: got {width}x{height}, expected {TARGET_WIDTH}x{TARGET_HEIGHT}"
        )

    print(f"Verified {target_file.name}: {width}x{height}")

    if not keep_originals:
        source_file.unlink()


def main() -> int:
    args = parse_args()

    if FFMPEG_PATH is None:
        print("ffmpeg was not found next to the script, in a parent TOOLS/ffmpeg folder, or in PATH.", file=sys.stderr)
        return 1

    if FFPROBE_PATH is None:
        print("ffprobe was not found next to the script, in a parent TOOLS/ffmpeg folder, or in PATH.", file=sys.stderr)
        return 1

    source_files = get_source_files(args.inputs)

    if not source_files:
        print("No JPG, JPEG, PNG, or GIF files were found in the provided inputs.")
        return 0

    converted_count = 0

    for source_file in source_files:
        convert_file(source_file, keep_originals=args.keep_originals)
        converted_count += 1

    print(
        f"Done. Converted {converted_count} file(s) to WebP at exact {TARGET_WIDTH}x{TARGET_HEIGHT} with alien- filename prefix."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())