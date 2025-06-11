# image_splitter.py
import os
from PIL import Image
import argparse


def split_image_horizontally(image_path, left_output_folder, right_output_folder, split_width=1920):
    """
    Splits an image horizontally at a specified width.
    Saves the left part to left_output_folder and right part to right_output_folder.
    Deletes the original image file after successful splitting.
    """
    try:
        img = Image.open(image_path)
        img_width, img_height = img.size

        if img_width <= split_width:
            print(
                f"Skipping split for '{os.path.basename(image_path)}': image width ({img_width}) is not greater than split_width ({split_width}).")
            return

        base_name = os.path.splitext(os.path.basename(image_path))[0]

        # Left part
        left_box = (0, 0, split_width, img_height)
        left_part = img.crop(left_box)
        left_path = os.path.join(left_output_folder, f"{base_name}-L.jpg")
        left_part.save(left_path, "JPEG")
        print(f"Split '{os.path.basename(image_path)}': Saved left part to '{os.path.basename(left_path)}'")

        # Right part
        right_box = (split_width, 0, img_width, img_height)
        right_part = img.crop(right_box)
        right_path = os.path.join(right_output_folder, f"{base_name}-R.jpg")
        right_part.save(right_path, "JPEG")
        print(f"Split '{os.path.basename(image_path)}': Saved right part to '{os.path.basename(right_path)}'")

        # --- New: Delete the original file after successful splitting ---
        os.remove(image_path)
        print(f"Deleted original file: '{os.path.basename(image_path)}'")
        # --- End New ---

    except Exception as e:
        print(f"Error splitting or deleting image '{os.path.basename(image_path)}': {e}")


def main():
    parser = argparse.ArgumentParser(description="Split image files horizontally.")
    parser.add_argument("--path", type=str, default=".",
                        help="Path to the folder containing image files (default: current directory).")
    parser.add_argument("--filename", type=str, default=None,
                        help="Start processing from this filename (lexical order). If not provided, starts from the first relevant file.")
    parser.add_argument("--split_width", type=int, default=1920,
                        help="Width at which to split the images horizontally (default: 1920).")
    args = parser.parse_args()

    folder_path = os.path.abspath(args.path)
    if not os.path.isdir(folder_path):
        print(f"Error: Path '{folder_path}' is not a valid directory.")
        return

    print(f"\n--- Starting image splitting in '{folder_path}' ---")
    print(f"Parameters: Start Filename='{args.filename}', Split Width={args.split_width}")

    # Create subfolders for split images
    left_splits_folder = os.path.join(folder_path, "_left_splits")
    right_splits_folder = os.path.join(folder_path, "_right_splits")
    os.makedirs(left_splits_folder, exist_ok=True)
    os.makedirs(right_splits_folder, exist_ok=True)
    print(f"Left split images will be saved to: '{left_splits_folder}'")
    print(f"Right split images will be saved to: '{right_splits_folder}'")

    image_extensions = (".jpg", ".jpeg", ".png")
    all_original_image_files = sorted([f for f in os.listdir(folder_path)
                                       if f.lower().endswith(image_extensions)
                                       and os.path.isfile(os.path.join(folder_path, f))
                                       and "-DUP" not in f])  # Exclude DUP files from splitting

    relevant_files_for_splitting = []
    if args.filename:
        found_start_file = False
        for f in all_original_image_files:
            if f >= args.filename:
                relevant_files_for_splitting.append(f)
                found_start_file = True
            elif found_start_file:  # After finding the start file, add all subsequent files
                relevant_files_for_splitting.append(f)
    else:
        relevant_files_for_splitting = all_original_image_files

    if not relevant_files_for_splitting:
        print(
            f"No relevant image files found in '{folder_path}' to split (starting from '{args.filename}' if provided).")
        return

    for filename in relevant_files_for_splitting:
        full_path = os.path.join(folder_path, filename)
        split_image_horizontally(full_path, left_splits_folder, right_splits_folder, args.split_width)

    print("\n--- Image splitting complete ---")


if __name__ == "__main__":
    main()