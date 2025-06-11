# Image Processing Workflow

This repository contains a set of Python scripts designed to automate common image processing tasks: horizontally splitting images and detecting visual duplicates using the Structural Similarity Index (SSIM). The workflow is modular, allowing you to run each task independently or as part of a combined process.

---

## Features

This project includes three main scripts:

* **`image_splitter.py`**:
    * Splits `.jpg` or `.png` images horizontally at a specified width.
    * Saves the left and right portions into dedicated `_left_splits` and `_right_splits` subfolders within the original image directory.
    * **Deletes the original image file** after successful splitting to save space.
    * Supports optional starting filename and target directory.

* **`image_comparator.py`**:
    * Compares images visually to detect duplicates using the **Structural Similarity Index (SSIM)**.
    * Focuses comparison on an "inner rectangle" of the images (configurable percentage).
    * Identifies and renames duplicate files by appending `-DUP` to their filename (e.g., `image-DUP.jpg`).
    * Intelligently handles chains of duplicate files, marking all in one pass.
    * Supports optional starting filename and target directory.

* **`main.py`**:
    * Orchestrates the full workflow by calling `image_splitter.py` first, followed by `image_comparator.py` on both the `_left_splits` and `_right_splits` folders.
    * Provides a single entry point for automated processing.

---

## Prerequisites

Before you begin, ensure you have the following installed:

* **Python 3.x**
* **Git Bash** (or any command-line environment that supports Python execution)

You'll also need to install the required Python libraries. Open your Git Bash or command prompt and run:

```bash
pip install Pillow numpy scikit-image
```

## Usage
Place your original `.jpg` or `.png` image files in the directory you intend to process (e.g., `c:\temp`).

#### Running Individual Scripts
You can run `image_splitter.py` and `image_comparator.py` independently.

`image_splitter.py`
This script takes original images, splits them, and moves the split parts to `_left_splits` and `_right_splits` folders. It then deletes the original files.

### Basic Usage (process all images in current directory):

```
python image_splitter.py
```

### Process images in a specific path:

```
python image_splitter.py --path "c:\temp"
```

### Process images starting from a specific filename (lexical order) in a given path:

```
python image_splitter.py --path "c:\temp" --filename "2025-06-03-09_06_21-001.jpg"
```

### Customize the split width:

```
python image_splitter.py --path "c:\temp" --split_width 1280
```

`image_comparator.py`
This script detects duplicate images within a specified folder. It will mark duplicates by appending -DUP to their filenames.

### Basic Usage (detect duplicates in current directory):

```
python image_comparator.py
```

Detect duplicates in the `_left_splits` folder (after running `image_splitter.py`):

```
python image_comparator.py --path "c:\temp\_left_splits"
```

Detect duplicates in `_right_splits` folder, starting from a specific filename:
```
python image_comparator.py --path "c:\temp\_right_splits" --filename "2025-06-03-09_06_21-001-R.jpg"
```
### Customize comparison parameters:

```
python image_comparator.py --path "c:\temp\_left_splits" --inner_rect_percent 0.85 --ssim_threshold 0.90
```

* `--inner_rect_percent`: Adjusts the size of the inner rectangle used for comparison (e.g., `0.90` for 90%).

* `--ssim_threshold`: Crucial for sensitivity! This is an SSIM value (0.0 to 1.0). Images with an SSIM score below this threshold are considered "materially different."

  * Lower value (e.g., `0.80`): More tolerant to differences, more likely to mark files as DUP.

  * Higher value (e.g., `0.98`): Less tolerant to differences, more likely to mark files as unique.

  * You'll likely need to experiment with this value for your specific images.

### Running the Main Workflow (`main.py`)
This script runs the entire sequence: first splitting original images, then running duplicate detection on both `_left_splits` and `_right_splits` folders.

### Basic Usage (run full workflow in current directory):
```
python main.py
```
Run full workflow in a specific directory, starting from a filename:
```
python main.py --path "c:\temp" --start_filename "2025-06-03-09_06_21-001.jpg"
```
Run with custom splitting and comparison parameters:
```
python main.py --path "c:\temp" --split_width 1600 --ssim_threshold 0.98
```
## Important Notes & Warnings
* **Backup Your Files!** This script modifies and deletes files. Always back up your original images before running this script to prevent accidental data loss.

* **Threshold Tuning**: The `--ssim_threshold` is critical for accurate duplicate detection. Experiment with different values on a sample set of your images to find what best defines "material difference" for your use case.

* **Grayscale Conversion**: Images are converted to grayscale for SSIM comparison. This might affect detection if color is the primary differentiator for duplicates.

* **Folder Structure**: The script creates `_left_splits` and `_right_splits` subfolders within your target directory. Do not manually modify the contents of these folders while the script is running.
