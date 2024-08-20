import os
import shutil
import argparse
import time
import warnings
from PIL import Image
from PIL.Image import DecompressionBombWarning
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Style, init


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


class Pixsort:
    def __init__(self, input_folder, output_folder, action):
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.action = action
        self.summary = {
            'moved_files': 0,
            'failed_files': 0,
            'total_size': 0
        }

    @staticmethod
    def log_error(file_path, error_message):
        """Log file paths that have errors."""
        log_file_path = os.path.join(os.getcwd(), 'logs.txt')

        file_size = os.path.getsize(
            file_path) if os.path.exists(file_path) else 0

        with open(log_file_path, 'a') as log_file:
            log_file.write(
                f"{file_path} | {error_message} | Size: {file_size} bytes\n")

    @staticmethod
    def classify_image(image_path):
        """Classify image based on its resolution."""
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error', DecompressionBombWarning)
                with Image.open(image_path) as img:
                    width, height = img.size

                    for category, (w, h) in sorted(RESOLUTION_CATEGORIES.items(), key=lambda item: item[1], reverse=True):
                        if width >= w and height >= h:
                            return category
                    return 'Unclassified'
        except DecompressionBombWarning as e:
            Pixsort.log_error(image_path, str(e))
            print(Fore.YELLOW +
                  f"Decompression bomb warning for {image_path}. Path logged to logs.txt.")
            return 'Warning'
        except Exception as e:
            Pixsort.log_error(image_path, f"{e}")
            print(Fore.RED + f"Error processing {image_path}: {e}")
            return 'Error'

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
            else:
                destination_folder = os.path.join(
                    self.output_folder, 'Unclassified')

            os.makedirs(destination_folder, exist_ok=True)
            destination_path = os.path.join(
                destination_folder, os.path.basename(file_path))

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

            self.summary['total_size'] += os.path.getsize(destination_path)
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


def main():
    print(Fore.CYAN + "PixSort - Created with love by E4CRYPT3D")

    parser = argparse.ArgumentParser(
        description="Sort images into folders based on resolution.")
    parser.add_argument('-i', '--input', required=True,
                        help='Input folder containing images.')
    parser.add_argument('-o', '--output', required=False,
                        help='Output folder to store sorted images.',
                        default=os.path.join(os.getcwd(), 'Sorted_images'))
    parser.add_argument('--action', choices=['move', 'copy'],
                        default='move', help='Choose whether to move or copy the files.')

    args = parser.parse_args()

    input_folder = os.path.abspath(args.input)
    output_folder = os.path.abspath(args.output)
    action = args.action

    # Clear previous logs
    log_file_path = os.path.join(output_folder, 'logs.txt')
    if os.path.exists(log_file_path):
        os.remove(log_file_path)

    sorter = Pixsort(input_folder, output_folder, action)

    start_time = time.time()
    sorter.sort_images()
    elapsed_time = time.time() - start_time

    print("\n" + Fore.YELLOW + "Summary:")
    print(
        f"Total files processed: {sorter.summary['moved_files'] + sorter.summary['failed_files']}")
    print(f"Files successfully {action}d: {sorter.summary['moved_files']}")
    print(f"Files failed to {action}: {sorter.summary['failed_files']}")
    print(
        f"Total data size {action}d: {sorter.summary['total_size'] / (1024 * 1024):.2f} MB")
    print(f"Total time taken: {elapsed_time:.2f} seconds.")
    print(Fore.YELLOW + f"Check logs.txt for files that triggered warnings or errors.")


if __name__ == "__main__":
    main()
