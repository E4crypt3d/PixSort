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
    'Low': (0, 0)  # Default category for resolutions below SD
}

# Supported image formats
SUPPORTED_FORMATS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp', '.jfif', '.heif', '.heic', '.psd', '.ico', '.cur', '.tga', '.dng', '.nef', '.cr2', '.orf', '.sr2',
                     '.arw', '.raf', '.dcr', '.k25', '.kdc', '.raw', '.3fr', '.ari', '.srw', '.dcs', '.drf', '.mef', '.nrw', '.pef', '.ptx', '.pxn', '.rw2', '.rwl', '.srw', '.x3f', '.xrf')
# Supported video formats
SUPPORTED_VIDEO_FORMATS = ('.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv',
                           '.webm', '.mpeg', '.mpg', '.3gp', '.m4v', '.m2ts', '.ts', '.vob', '.ogv')


class Pixsort:
    def __init__(self, input_folder, output_folder, action):
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.action = action
        self.summary = {
            'moved_files': 0,
            'failed_files': 0,
            'total_size': 0,
            'available_space': 0,
            'folder_summary': {}  # To track number of files and sizes for each resolution folder
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

                    # Define the sorted resolution categories for efficient classification
                    sorted_categories = sorted(
                        RESOLUTION_CATEGORIES.items(),
                        key=lambda item: item[1],
                        reverse=True
                    )

                    for category, (w, h) in sorted_categories:
                        if width >= w and height >= h:
                            return category

                    # Return 'Unclassified' if no category matches
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

    def check_disk_space(self):
        """Check available disk space in the output folder's drive."""
        try:
            total, used, free = psutil.disk_usage(self.output_folder).total, psutil.disk_usage(
                self.output_folder).used, psutil.disk_usage(self.output_folder).free
            return free
        except Exception as e:
            print(Fore.RED + f"Error checking disk space: {e}")
            return 0

    def process_image(self, file_path):
        """Process and move or copy a single image to the appropriate folder."""
        try:
            if file_path.lower().endswith(SUPPORTED_FORMATS):
                resolution_type = self.classify_image(file_path)
                if resolution_type == 'Warning':
                    destination_folder = os.path.join(
                        self.output_folder, 'Unsorted')
                elif resolution_type and resolution_type != 'Error':
                    destination_folder = os.path.join(
                        self.output_folder, resolution_type)
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

            # Check disk space before copying
            if self.action == 'copy':
                file_size = os.path.getsize(file_path)
                available_space = self.check_disk_space()

                if available_space < file_size:
                    raise IOError("Insufficient disk space to copy the file.")

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

            # Update folder summary
            if destination_folder not in self.summary['folder_summary']:
                self.summary['folder_summary'][destination_folder] = {
                    'count': 0, 'size': 0}
            self.summary['folder_summary'][destination_folder]['count'] += 1
            self.summary['folder_summary'][destination_folder]['size'] += file_size

        except IOError as e:
            if "Insufficient disk space" in str(e):
                self.log_error(file_path, f"Disk full: {e}")
                print(Fore.RED + "Error: Insufficient disk space. Exiting...")
                sys.exit(1)  # Exit the script with an error code
            else:
                self.log_error(file_path, f"Failed to {self.action}: {e}")
                print(Fore.RED + f"Failed to {self.action} {file_path}: {e}")
                self.summary['failed_files'] += 1

        except Exception as e:
            self.log_error(file_path, f"Failed to {self.action}: {e}")
            print(Fore.RED + f"Failed to {self.action} {file_path}: {e}")
            self.summary['failed_files'] += 1

    def sort_images(self):
        """Sort images into folders based on their resolution."""
        os.makedirs(self.output_folder, exist_ok=True)

        image_files = []
        for root, dirs, files in os.walk(self.input_folder):
            for file in files:
                file_path = os.path.join(root, file)
                image_files.append(file_path)

        # Use a ThreadPoolExecutor with a dynamic number of workers
        num_workers = max(2, min(int((os.cpu_count() or 1) * 2), 8) if not hasattr(os, 'getloadavg')
                          else min(int((os.cpu_count() or 1) * (1 / (1 + os.getloadavg()[0] / (os.cpu_count() or 1)))), 8))

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {executor.submit(
                self.process_image, file_path): file_path for file_path in image_files}

            for future in as_completed(futures):
                file_path = futures[future]
                try:
                    future.result()  # Ensures any raised exceptions are caught
                except Exception as e:
                    self.log_error(file_path, f"Failed to {self.action}: {e}")
                    print(
                        Fore.RED + f"Failed to {self.action} {file_path}: {e}")

    def handle_keyboard_interrupt(self):
        """Handle keyboard interrupt gracefully."""
        print(Fore.RED + "\nOperation interrupted by user. Exiting...")

    def show_summary(self, elapsed_time):
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
            print(Fore.YELLOW + "No files were sorted into specific resolution folders.")

        print(Fore.CYAN + "=" * 60)
        print(Fore.YELLOW + "Check logs.txt for files that triggered warnings or errors.")


def main():
    print(Fore.CYAN + "PixSort - Created with love by E4CRYPT3D")
    print(Fore.CYAN + "=" * 60)

    parser = argparse.ArgumentParser(
        description="Sort images and videos into folders based on their resolution or file type."
    )
    parser.add_argument('-i', '--input', required=True,
                        help='Path to the input folder containing images and videos.')
    parser.add_argument('-o', '--output', required=False,
                        help='Path to the output folder where sorted files will be stored. Defaults to a folder named "Sorted_images" in the current directory.',
                        default=os.path.join(os.getcwd(), 'Sorted_images'))
    parser.add_argument('--action', choices=['move', 'copy'], default='move',
                        help='Action to perform on files: move or copy. Default is "move".')

    args = parser.parse_args()

    input_folder = os.path.abspath(args.input)
    output_folder = os.path.abspath(args.output)
    action = args.action

    # Validate input folder
    if not os.path.isdir(input_folder):
        print(
            Fore.RED + f"Error: The input folder '{input_folder}' does not exist or is not a directory.")
        sys.exit(1)

    # Clear previous logs
    log_file_path = os.path.join(os.getcwd(), 'logs.txt')
    if os.path.exists(log_file_path):
        os.remove(log_file_path)

    sorter = Pixsort(input_folder, output_folder, action)

    start_time = time.time()
    try:
        sorter.sort_images()
    except KeyboardInterrupt:
        sorter.handle_keyboard_interrupt()
    finally:
        elapsed_time = time.time() - start_time
        sorter.show_summary(elapsed_time)


if __name__ == "__main__":
    main()
