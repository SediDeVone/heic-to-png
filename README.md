# HEIC to PNG Converter

A simple and efficient tool to convert HEIC images to PNG format.

## Features

- **Native macOS support**: Uses the built-in `sips` command for fast conversion
- **Cross-platform fallback**: Uses Pillow with pillow-heif on non-macOS systems
- **Batch conversion**: Converts all HEIC files in a directory
- **Overwrite protection**: Skips existing files by default

## Installation

```bash
pip install -r requirements.txt
```

> **Note**: On macOS, the native `sips` command is used by default, so Python dependencies are optional.

## Usage

### Command Line

Basic usage (converts files in `./data` directory):
```bash
python main.py
```

With custom directories:
```bash
python main.py -i /path/to/input -o /path/to/output
```

Overwrite existing files:
```bash
python main.py --overwrite
```

### Programmatic Usage

```python
from main import convert_heic_to_png

# Basic usage
count = convert_heic_to_png()

# With custom directories
count = convert_heic_to_png(
    input_dir="./my_images",
    output_dir="./converted",
    overwrite=False
)

print(f"Converted {count} file(s)")
```

## Requirements

- Python 3.8+
- macOS (uses native `sips`) **OR** Pillow with pillow-heif

## License

MIT
