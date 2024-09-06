import os
import shutil
import argparse
import time
import warnings
from PIL import Image
from PIL.Image import DecompressionBombWarning
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Style, init
import psutil
import sys


init(autoreset=True)

# Resolution categories
RESOLUTION_CATEGORIES = {
    '16K': (15360, 8640),
    '12K': (12288, 6480),
    '10K': (10240, 4320),
    '8K': (7680, 4320),
    '5K': (5120, 2880),
    '4K': (3840, 2160),
    '2K': (2560, 1440),
    'Full HD': (1920, 1080),
    'HD': (1280, 720),
    'SD': (720, 480),
    'Low': (0, 0)  # Default
}

# File size categories for images
FILE_SIZE_CATEGORIES = {
    'Small': (0, 5 * 1024 * 1024),  # Up to 5 MB
    'Medium': (5 * 1024 * 1024, 20 * 1024 * 1024),  # 5 MB to 20 MB
    'Large': (20 * 1024 * 1024, 50 * 1024 * 1024),  # 20 MB to 50 MB
    'Extra Large': (50 * 1024 * 1024, float('inf')),  # Over 50 MB
}

# Supported image formats
SUPPORTED_FORMATS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp', '.jfif', '.heif', '.heic', '.psd', '.ico', '.cur', '.tga', '.dng', '.nef', '.cr2', '.orf', '.sr2',
                     '.arw', '.raf', '.dcr', '.k25', '.kdc', '.raw', '.3fr', '.ari', '.srw', '.dcs', '.drf', '.mef', '.nrw', '.pef', '.ptx', '.pxn', '.rw2', '.rwl', '.srw', '.x3f', '.xrf')
# Supported video formats
SUPPORTED_VIDEO_FORMATS = ('.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv',
                           '.webm', '.mpeg', '.mpg', '.3gp', '.m4v', '.m2ts', '.ts', '.vob', '.ogv')


class Pixsort:
    def __init__(self, input_folder, output_folder, action, sort_by):
        """
        Initialize Pixsort with the given parameters.

        Parameters:
            input_folder (str): The folder containing the images to sort.
            output_folder (str): The folder where the sorted images will be moved or copied.
            action (str): The action to perform. Either 'move' or 'copy'.
            sort_by (str): The criteria for sorting. Either 'resolution' or 'size'.
        """
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.action = action
        self.sort_by = sort_by
        self.summary = {
            'moved_files': 0,
            'failed_files': 0,
            'total_size': 0,
            'folder_summary': {}
        }

    @staticmethod
    def log_error(file_path, error_message):
        """Log file paths that have errors."""
        log_file_path = os.path.join(os.getcwd(), 'logs.txt')

        try:
            file_size = os.path.getsize(
                file_path) if os.path.exists(file_path) else 0
            with open(log_file_path, 'a') as log_file:
                log_file.write(
                    f"{file_path} | {error_message} | Size: {file_size} bytes\n")
        except Exception as e:
            print(Fore.RED + f"Failed to log error for {file_path}: {e}")

    def classify_image(self, image_path):
        """Classify image based on its resolution."""
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error', DecompressionBombWarning)
                with Image.open(image_path) as img:
                    width, height = img.size

                    sorted_categories = sorted(
                        RESOLUTION_CATEGORIES.items(),
                        key=lambda item: item[1],
                        reverse=True
                    )

                    for category, (w, h) in sorted_categories:
                        if width >= w and height >= h:
                            return category

                    return 'Unclassified'

        except DecompressionBombWarning as e:
            self.log_error(image_path, f"Decompression bomb warning: {e}")
            print(
                Fore.YELLOW + f"Decompression bomb warning for {image_path}. Path logged to logs.txt.")
            return 'Warning'

        except FileNotFoundError:
            self.log_error(image_path, "File not found")
            print(Fore.RED + f"File not found: {image_path}")
            return 'Error'

        except IOError as e:
            self.log_error(image_path, f"IOError: {e}")
            print(Fore.RED + f"IOError processing {image_path}: {e}")
            return 'Error'

        except Exception as e:
            self.log_error(image_path, f"Unexpected error: {e}")
            print(Fore.RED + f"Unexpected error processing {image_path}: {e}")
            return 'Error'

    def classify_by_size(self, file_path):
        """Classify image based on its file size."""
        try:
            file_size = os.path.getsize(file_path)

            for category, (min_size, max_size) in FILE_SIZE_CATEGORIES.items():
                if min_size <= file_size < max_size:
                    return category

            return 'Unclassified'

        except FileNotFoundError:
            self.log_error(file_path, "File not found")
            print(Fore.RED + f"File not found: {file_path}")
            return 'Error'

        except IOError as e:
            self.log_error(file_path, f"IOError: {e}")
            print(Fore.RED + f"IOError processing {file_path}: {e}")
            return 'Error'

        except Exception as e:
            self.log_error(file_path, f"Unexpected error: {e}")
            print(Fore.RED + f"Unexpected error processing {file_path}: {e}")
            return 'Error'

    def check_disk_space(self):
        """Check available disk space in the output folder's drive."""
        try:
            return psutil.disk_usage(self.output_folder).free
        except Exception as e:
            print(Fore.RED + f"Error checking disk space: {e}")
            return 0

    def process_image(self, file_path):
        """Process and move or copy a single image to the appropriate folder."""
        try:
            if file_path.lower().endswith(SUPPORTED_FORMATS):
                if self.sort_by == 'resolution':
                    category = self.classify_image(file_path)
                elif self.sort_by == 'size':
                    category = self.classify_by_size(file_path)
                else:
                    category = 'Unclassified'

                if category == 'Warning':
                    destination_folder = os.path.join(
                        self.output_folder, 'Unsorted')
                elif category and category != 'Error':
                    destination_folder = os.path.join(
                        self.output_folder, category)
                else:
                    destination_folder = os.path.join(
                        self.output_folder, 'Unclassified')
            elif file_path.lower().endswith(SUPPORTED_VIDEO_FORMATS):
                destination_folder = os.path.join(self.output_folder, 'Videos')
            else:
                destination_folder = os.path.join(
                    self.output_folder, 'Unclassified')

            os.makedirs(destination_folder, exist_ok=True)
            destination_path = os.path.join(
                destination_folder, os.path.basename(file_path))

            if self.action == 'copy':
                file_size = os.path.getsize(file_path)
                available_space = self.check_disk_space()

                if available_space < file_size:
                    self.log_error(
                        file_path, "Insufficient disk space to copy the file.")
                    print(Fore.RED + "Error: Insufficient disk space. Exiting...")
                    sys.exit(1)

            if self.action == 'move':
                shutil.move(file_path, destination_path)
                self.summary['moved_files'] += 1
                print(
                    Fore.GREEN + f"Moved {os.path.basename(file_path)} to {destination_folder}")
            elif self.action == 'copy':
                shutil.copy2(file_path, destination_path)
                self.summary['moved_files'] += 1
                print(
                    Fore.BLUE + f"Copied {os.path.basename(file_path)} to {destination_folder}")

            file_size = os.path.getsize(destination_path)
            self.summary['total_size'] += file_size

            if destination_folder not in self.summary['folder_summary']:
                self.summary['folder_summary'][destination_folder] = {
                    'count': 0, 'size': 0}
            self.summary['folder_summary'][destination_folder]['count'] += 1
            self.summary['folder_summary'][destination_folder]['size'] += file_size

        except Exception as e:
            self.log_error(file_path, f"Failed to {self.action}: {e}")
            print(Fore.RED + f"Failed to {self.action} {file_path}: {e}")
            self.summary['failed_files'] += 1

    def sort_images(self):
        """Sort images into folders based on their resolution or file size."""
        os.makedirs(self.output_folder, exist_ok=True)

        image_files = []
        for root, dirs, files in os.walk(self.input_folder):
            for file in files:
                file_path = os.path.join(root, file)
                image_files.append(file_path)

        num_workers = min(max(2, (os.cpu_count() or 1) * 2), 8)

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {executor.submit(
                self.process_image, file_path): file_path for file_path in image_files}

            for future in as_completed(futures):
                file_path = futures[future]
                try:
                    future.result()
                except Exception as e:
                    self.log_error(file_path, f"Failed to {self.action}: {e}")
                    print(
                        Fore.RED + f"Failed to {self.action} {file_path}: {e}")

    def handle_keyboard_interrupt(self) -> None:
        """Handle keyboard interrupt gracefully."""
        print("\nOperation interrupted by user. Exiting...")

    def show_summary(self, elapsed_time):
        """
        Print a summary of the sorting operation.
        """
        script_name = "PixSort"
        creator_name = "E4CRYPT3D"
        available_space_mb = self.check_disk_space() / (1024 * 1024)

        # Header
        print(Fore.CYAN + "=" * 60)
        print(Fore.CYAN + Style.BRIGHT +
              f"{script_name} - Created by {creator_name}")
        print(Fore.CYAN + "=" * 60)

        # Summary Statistics
        print(Fore.GREEN + Style.BRIGHT +
              f"Total files processed: {self.summary['moved_files'] + self.summary['failed_files']}")
        print(Fore.GREEN + Style.BRIGHT +
              f"Files successfully {self.action}d: {self.summary['moved_files']}")
        print(Fore.RED + Style.BRIGHT +
              f"Files failed to {self.action}: {self.summary['failed_files']}")
        print(Fore.YELLOW + Style.BRIGHT +
              f"Total data size {self.action}d: {self.summary['total_size'] / (1024 * 1024):.2f} MB")
        print(Fore.YELLOW + Style.BRIGHT +
              f"Available disk space: {available_space_mb:.2f} MB")
        print(Fore.CYAN + Style.BRIGHT +
              f"Total time taken: {elapsed_time:.2f} seconds.")
        print(Fore.CYAN + "=" * 60)

        # Detailed Folder Summary
        print(Fore.CYAN + Style.BRIGHT + "Detailed Folder Summary:")
        print(Fore.CYAN + "-" * 60)

        if self.summary['folder_summary']:
            for folder, details in self.summary['folder_summary'].items():
                count = details['count']
                size_mb = details['size'] / (1024 * 1024)
                print(Fore.MAGENTA +
                      f"• {folder}: {count} files, {size_mb:.2f} MB")
        else:
            print(Fore.YELLOW + "No files were sorted into specific folders.")

        print(Fore.CYAN + "=" * 60)
        print(Fore.YELLOW + "Check logs.txt for files that triggered warnings or errors.")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Sort images into folders based on resolution or file size.')
    parser.add_argument('-i', '--input', required=True,
                        help='Path to the folder containing images to sort.')
    parser.add_argument('-o', '--output', default=os.path.join(os.getcwd(), 'Sorted_images'),
                        help='Path to the folder where sorted images will be moved or copied.')
    parser.add_argument('-a', '--action', choices=['move', 'copy'], default='move',
                        help='Action to perform: move or copy the images.')
    parser.add_argument('-s', '--sort_by', choices=['resolution', 'size'], default='resolution',
                        help='Sort images by resolution or file size. Default is "resolution".')
    return parser.parse_args()


def main():
    print(Fore.CYAN + "PixSort - Created with love by E4CRYPT3D")
    print(Fore.CYAN + "=" * 60)

    args = parse_args()

    pixsort = Pixsort(args.input, args.output, args.action, args.sort_by)

    # Clearing logs
    log_file_path = os.path.join(os.getcwd(), 'logs.txt')
    if os.path.exists(log_file_path):
        os.remove(log_file_path)

    start_time = time.time()
    try:
        pixsort.sort_images()
    except KeyboardInterrupt:
        pixsort.handle_keyboard_interrupt()
    finally:
        elapsed_time = time.time() - start_time
        pixsort.show_summary(elapsed_time)


if __name__ == "__main__":
    main()
