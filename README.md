# PixSort Documentation

## Overview

PixSort is a Python script designed to help users organize their image files by sorting them into folders based on their resolution. The script can move or copy images from a source directory to a target directory, categorizing them into folders such as `'16K'`, `'12K'`, `'8K'`, etc., according to their resolution. The script also handles errors and warnings, logging them for review.

## Features

- `Sort Images`: Organizes images into folders based on their resolution.
- `Move or Copy`: Option to either move or copy the images to the target directory.
- `Multi-threaded Processing`: Utilizes multiple threads to speed up processing.
- `Error Logging`: Logs errors and warnings related to image processing.

## User Documentation

Prerequisites

- `Python`: Ensure Python 3.6 or higher is installed.

- Libraries: The script requires the following Python libraries:

```
PIL (Pillow)
colorama
concurrent.futures
```

Install these libraries using pip:

```
pip install pillow colorama
```

## How to Use

Prepare Your Directories:

- `Input Folder`: The folder containing the images you want to sort.
- `Output Folder`: The folder where sorted images will be saved. If not specified, defaults to `Sorted_images` in the current working directory.
- Run the Script:
- Open a terminal or command prompt and run the following command:

```
python pixsort.py -i /path/to/input/folder -o /path/to/output/folder --action move
```

Replace `/path/to/input/folder` with the path to your input directory and `/path/to/output/folder` with your desired output directory. Use `--action copy` if you prefer to copy files instead of moving them.

### View Results:

- `Sorted Images`: Check the output folder for sorted images categorized by resolution.
- `Logs`: Check `logs.txt` in the output folder for any warnings or errors encountered during processing.

## Example

To sort images in `C:/Users/YourName/Pictures` and move them to `C:/Users/YourName/SortedImages`, run:

```
python pixsort.py -i C:/Users/YourName/Pictures -o C:/Users/YourName/SortedImages --action move
```

## Developer Documentation

Code Overview

- `log_error(file_path, error_message)`: Logs errors related to image processing.
- `classify_image(image_path)`: Determines the resolution category of an image.
- `process_image(file_path, output_folder, action, summary)`: Processes individual image files by moving or copying them to appropriate folders.
- `sort_images(input_folder, output_folder, action, summary)`: Main function that traverses the input folder and uses threads to process images.
- `main()`: Entry point of the script, handles argument parsing and summarizes results.

### Libraries Used

- `Pillow`: For image processing.
- `Colorama`: For colored terminal output.
- `Concurrent Futures`: For multi-threading to improve performance.

### Adding New Features

- Extend Resolution Categories:
  Update the `RESOLUTION_CATEGORIES` dictionary to include new resolution categories.

### Add Support for More Formats:

Modify the `SUPPORTED_FORMATS` tuple to include additional image file extensions.

### Improve Error Handling:

Add more specific exceptions or error handling mechanisms in the `process_image` function to handle different types of image-related issues.

### Code Structure

- `Logging`: Implemented via log_error function which appends error messages to `logs.txt`.
- `Image Classification`: Uses resolution categories to classify images.
- `Multithreading`: Utilized to handle large volumes of images efficiently.

### Development Setup

- Clone Repository:

```
git clone https://github.com/E4crypt3d/pixsort.git
cd pixsort
```

- Install Dependencies:

```
pip install -r requirements.txt
```
