# Pixsort

Pixsort is a Python script that sorts images into folders based on their resolution or file size. It can move or copy images to the specified destination directory.

## Features

- Sort by Resolution: Categorizes images into folders like 4K, HD, etc.
- Sort by File Size: Categorizes images into folders such as Small, Medium, Large, and Extra Large.
- Move or Copy: Choose to either move or copy images.
- Detailed Logging: Logs errors and warnings to a file.

## Installation

Ensure you have Python and the necessary packages installed. You can install the required packages using:

```bash
pip install pillow colorama psutil
```

```bash
python pixsort.py -i INPUT_FOLDER -o OUTPUT_FOLDER -a ACTION -s SORT_BY
```

## Arguments

- `-i`, `--input`: Path to the folder containing images.
- `-o`, `--output`: Path to the destination folder for sorted images. Default is `Sorted_images`.
- `-a`, `--action`: Action to perform (`move` or `copy`). Default is `move`.
- `-s`, `--sort_by`: Criteria for sorting (`resolution` or `size`). Default is `resolution`.

### Example

```bash
python pixsort.py -i /path/to/images -o /path/to/sorted -a move -s size
```
