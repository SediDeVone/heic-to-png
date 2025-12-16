"""
HEIC to PNG Image Converter

Converts HEIC images to PNG format using macOS sips (native) or Pillow.

Usage Examples:
    python main.py                          # Convert files in ./data
    python main.py -i ./photos -o ./output  # Custom directories
    python main.py --overwrite              # Overwrite existing files
    python main.py -v                       # Enable verbose logging

Programmatic Usage:
    from main import convert_heic_to_png
    count = convert_heic_to_png("./my_images", "./converted", overwrite=False)
"""
from __future__ import annotations

import argparse
import logging
import subprocess
from pathlib import Path
from typing import Iterable, Tuple
import shutil

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

SUBPROCESS_TIMEOUT = 60


def _has_sips() -> bool:
    return shutil.which("sips") is not None


def _convert_with_sips(src: Path, dst: Path) -> Tuple[bool, str]:
    try:
        result = subprocess.run(
            ["sips", "-s", "format", "png", str(src), "--out", str(dst)],
            capture_output=True,
            text=True,
            check=False,
            timeout=SUBPROCESS_TIMEOUT,
        )
        if result.returncode == 0:
            return True, ""
        return False, result.stderr.strip() or result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, f"Conversion timed out after {SUBPROCESS_TIMEOUT} seconds"
    except Exception as e:
        return False, str(e)


def _convert_with_pillow(src: Path, dst: Path) -> Tuple[bool, str]:
    try:
        from PIL import Image  # type: ignore
        try:
            import pillow_heif  # type: ignore

            pillow_heif.register_heif_opener()
        except Exception:
            try:
                import pyheif  # type: ignore

                def _open_heif(path: Path):
                    heif_file = pyheif.read(path.read_bytes())
                    image = Image.frombytes(
                        heif_file.mode,
                        heif_file.size,
                        heif_file.data,
                        "raw",
                        heif_file.mode,
                        heif_file.stride,
                    )
                    return image

                img = _open_heif(src)
                img.save(dst, format="PNG")
                return True, ""
            except Exception as e2:
                return False, (
                    "Pillow HEIC support not available. Install 'pillow-heif' or 'pyheif'. "
                    f"Details: {e2}"
                )

        with Image.open(src) as im:
            im.save(dst, format="PNG")
        return True, ""
    except Exception as e:
        return False, str(e)


def iter_heic_files(directory: Path) -> Iterable[Path]:
    suffixes = {".heic", ".HEIC"}
    for p in directory.iterdir():
        if p.is_file() and p.suffix in suffixes:
            yield p


def convert_heic_to_png(
    input_dir: Path | str | None = None,
    output_dir: Path | str | None = None,
    overwrite: bool = False
) -> int:
    """
    Convert all .HEIC images from input_dir to .png.

    - input_dir: directory that contains .HEIC files. Defaults to '<project_root>/data'.
    - output_dir: where to place .png files. Defaults to input_dir.
    - overwrite: if False, existing .png files are skipped.

    Returns the number of files successfully converted.

    Raises:
        FileNotFoundError: If input_dir does not exist.
        NotADirectoryError: If input_dir is not a directory.
    """
    project_root = Path(__file__).resolve().parent
    in_dir = Path(input_dir) if input_dir else project_root / "data"
    out_dir = Path(output_dir) if output_dir else in_dir

    if not in_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {in_dir}")
    if not in_dir.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {in_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)

    use_sips = _has_sips()
    logger.info(f"Using {'sips' if use_sips else 'Pillow'} for conversion")

    converted = 0
    errors = []

    for src in iter_heic_files(in_dir):
        dst = out_dir / (src.stem + ".png")
        if dst.exists() and not overwrite:
            logger.debug(f"Skipping {src.name} (output already exists)")
            continue
        
        logger.info(f"Converting {src.name}...")
        
        if use_sips:
            ok, msg = _convert_with_sips(src, dst)
        else:
            ok, msg = _convert_with_pillow(src, dst)
        
        if ok:
            converted += 1
            logger.info(f"Successfully converted {src.name}")
        else:
            errors.append((src.name, msg))
            logger.error(f"Failed to convert {src.name}: {msg}")

    if errors:
        logger.warning(f"Completed with {len(errors)} error(s)")
    else:
        logger.info(f"Completed successfully. Converted {converted} file(s)")

    return converted


def main() -> None:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Convert HEIC images to PNG format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Convert files in ./data
  python main.py -i ./photos -o ./output  # Custom directories
  python main.py --overwrite              # Overwrite existing files
        """
    )
    parser.add_argument(
        "-i", "--input",
        metavar="DIR",
        help="Input directory containing HEIC files (default: ./data)"
    )
    parser.add_argument(
        "-o", "--output",
        metavar="DIR",
        help="Output directory for PNG files (default: same as input)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing PNG files"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose (debug) logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        count = convert_heic_to_png(args.input, args.output, args.overwrite)
        print(f"Converted {count} file(s) to PNG.")
    except (FileNotFoundError, NotADirectoryError) as e:
        logger.error(str(e))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
