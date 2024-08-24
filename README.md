# PixSort

PixSort is a Python script for sorting images and videos into folders based on their resolution or file type. It supports both moving and copying files and logs errors for troubleshooting.

## Features

- Sorts images and videos by resolution or type.
- Supports a wide range of image and video formats.
- Logs errors to `logs.txt`.
- Displays a detailed summary of processed files and folders.

## Requirements

Install dependencies using:

```bash
pip install pillow psutil colorama
```

### Usage

```bash
python pixsort.py -i <input_folder> -o <output_folder> --action <move|copy>
```

### Arguments

- `-i` / `--input`: Path to the input folder `(required)`.
- `-o` / `--output`: Path to the output folder `(default: Sorted_images in the current directory)`.
- `--action`: Action to perform `(move or copy, default: move)`.

### Example

```bash
python pixsort.py -i /path/to/input -o /path/to/output --action copy
```

### Error Logging

- Errors and warnings are logged to `logs.txt` in the script's directory.

#### Author

- Created with love by E4CRYPT3D.
