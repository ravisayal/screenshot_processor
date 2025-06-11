# main_processor.py
import os
import argparse
import shutil

# Import functions from the separate scripts
from image_splitter import split_image_horizontally
from image_comparator import run_duplicate_detection


def main():
    parser = argparse.ArgumentParser(description="Full image processing workflow: split and then detect duplicates.")
    parser.add_argument("--path", type=str, default=".",
                        help="Path to the main folder containing original image files (default: current directory).")
    parser.add_argument("--start_filename", type=str, default=None,
                        help="Start processing from this filename (lexical order). If not provided, starts from the first relevant original file.")
    parser.add_argument("--split_width", type=int, default=1920,
                        help="Width at which to split the images horizontally (default: 1920).")
    parser.add_argument("--inner_rect_percent", type=float, default=0.90,
                        help="Percentage of the inner rectangle to use for comparison (e.g., 0.90 for 90%%).")
    parser.add_argument("--ssim_threshold", type=float, default=0.95,
                        help="SSIM similarity threshold. Values below this are considered materially different (default: 0.95).")
    args = parser.parse_args()

    # --- Configuration ---
    TARGET_FOLDER = os.path.abspath(args.path)
    START_FILENAME = args.start_filename
    SPLIT_AT_WIDTH = args.split_width
    INNER_RECTANGLE_PERCENTAGE = args.inner_rect_percent
    SSIM_SIMILARITY_THRESHOLD = args.ssim_threshold

    if not os.path.isdir(TARGET_FOLDER):
        print(f"Error: Main path '{TARGET_FOLDER}' is not a valid directory.")
        return

    print(f"\n--- Starting Full Image Processing Workflow in '{TARGET_FOLDER}' ---")
    print(
        f"Global Parameters: Start Filename='{START_FILENAME}', Split Width={SPLIT_AT_WIDTH}, Inner Rectangle %={INNER_RECTANGLE_PERCENTAGE * 100}%, SSIM Threshold={SSIM_SIMILARITY_THRESHOLD}")

    # Create subfolders for split images
    left_splits_folder = os.path.join(TARGET_FOLDER, "_left_splits")
    right_splits_folder = os.path.join(TARGET_FOLDER, "_right_splits")
    os.makedirs(left_splits_folder, exist_ok=True)
    os.makedirs(right_splits_folder, exist_ok=True)
    print(f"Left split images will be saved to: '{left_splits_folder}'")
    print(f"Right split images will be saved to: '{right_splits_folder}'")

    image_extensions = (".jpg", ".jpeg", ".png")
    all_original_image_files = sorted([f for f in os.listdir(TARGET_FOLDER)
                                       if f.lower().endswith(image_extensions)
                                       and os.path.isfile(os.path.join(TARGET_FOLDER, f))
                                       and "-DUP" not in f])  # Exclude DUP files from splitting

    relevant_files_for_splitting = []
    if START_FILENAME:
        found_start_file = False
        for f in all_original_image_files:
            if f >= START_FILENAME:
                relevant_files_for_splitting.append(f)
                found_start_file = True
            elif found_start_file:  # After finding the start file, add all subsequent files
                relevant_files_for_splitting.append(f)
    else:
        relevant_files_for_splitting = all_original_image_files

    if not relevant_files_for_splitting:
        print(
            f"No relevant image files found in '{TARGET_FOLDER}' to split (starting from '{START_FILENAME}' if provided).")
        return

    # --- Step 1: Split images ---
    print(f"\n--- Step 1: Running Image Splitting ---")
    for filename in relevant_files_for_splitting:
        full_path = os.path.join(TARGET_FOLDER, filename)
        split_image_horizontally(full_path, left_splits_folder, right_splits_folder, SPLIT_AT_WIDTH)

    # --- Step 2: Run Duplicate Detection on Left Splits ---
    print(f"\n--- Step 2: Running Duplicate Detection for '{os.path.basename(left_splits_folder)}' ---")
    # For splits, we usually want to check all files in the subfolder regardless of original start_filename
    run_duplicate_detection(
        folder_to_check=left_splits_folder,
        start_filename_for_dup_check="",  # Check all files in the split folder
        inner_rect_percent=INNER_RECTANGLE_PERCENTAGE,
        ssim_similarity_threshold=SSIM_SIMILARITY_THRESHOLD
    )

    # --- Step 3: Run Duplicate Detection on Right Splits ---
    print(f"\n--- Step 3: Running Duplicate Detection for '{os.path.basename(right_splits_folder)}' ---")
    run_duplicate_detection(
        folder_to_check=right_splits_folder,
        start_filename_for_dup_check="",  # Check all files in the split folder
        inner_rect_percent=INNER_RECTANGLE_PERCENTAGE,
        ssim_similarity_threshold=SSIM_SIMILARITY_THRESHOLD
    )

    print("\n--- Full Image Processing Workflow Complete ---")


if __name__ == "__main__":
    main()