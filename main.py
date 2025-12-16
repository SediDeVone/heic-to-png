from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable, Tuple
import shutil


def _has_sips() -> bool:
    return shutil.which("sips") is not None


def _convert_with_sips(src: Path, dst: Path) -> Tuple[bool, str]:
    try:
        result = subprocess.run(
            ["sips", "-s", "format", "png", str(src), "--out", str(dst)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return True, ""
        return False, result.stderr.strip() or result.stdout.strip()
    except Exception as e:
        return False, str(e)


def _convert_with_pillow(src: Path, dst: Path) -> Tuple[bool, str]:
    try:
        # Lazy imports to keep startup fast and avoid hard dependency when using sips
        from PIL import Image  # type: ignore
        try:
            import pillow_heif  # type: ignore

            pillow_heif.register_heif_opener()
        except Exception:
            # If pillow-heif not available, try pyheif as a fallback loader
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

        # If pillow-heif registered, regular open works
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


def convert_heic_to_png(input_dir: Path | str = None, output_dir: Path | str | None = None, overwrite: bool = False) -> int:
    """
    Convert all .HEIC images from input_dir to .png.

    - input_dir: directory that contains .HEIC files. Defaults to '<project_root>/data'.
    - output_dir: where to place .png files. Defaults to input_dir.
    - overwrite: if False, existing .png files are skipped.

    Returns the number of files successfully converted.
    """
    project_root = Path(__file__).resolve().parent
    in_dir = Path(input_dir) if input_dir else project_root / "data"
    out_dir = Path(output_dir) if output_dir else in_dir

    out_dir.mkdir(parents=True, exist_ok=True)

    use_sips = _has_sips()
    converted = 0
    errors = []

    for src in iter_heic_files(in_dir):
        dst = out_dir / (src.stem + ".png")
        if dst.exists() and not overwrite:
            continue
        if use_sips:
            ok, msg = _convert_with_sips(src, dst)
        else:
            ok, msg = _convert_with_pillow(src, dst)
        if ok:
            converted += 1
        else:
            errors.append((src.name, msg))

    if errors:
        for name, msg in errors:
            print(f"Failed to convert {name}: {msg}")

    return converted


if __name__ == '__main__':
    count = convert_heic_to_png()
    print(f"Converted {count} file(s) to PNG in the 'data' directory.")
