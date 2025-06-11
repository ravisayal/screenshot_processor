# image_comparator.py
import os
from PIL import Image
import numpy as np
from skimage.metrics import structural_similarity as ssim
import argparse


def compare_images_visually(img1_path, img2_path, inner_rectangle_percentage, ssim_similarity_threshold):
    """
    Compares the inner rectangle (e.g., 90%) of two images using SSIM.
    Returns True if there's a material difference, False otherwise.
    A higher ssim_similarity_threshold means images must be very similar to be considered duplicates.
    """
    try:
        img1 = Image.open(img1_path).convert("L")  # Convert to grayscale
        img2 = Image.open(img2_path).convert("L")

        # Convert PIL Image to NumPy array for scikit-image
        img1_np = np.array(img1)
        img2_np = np.array(img2)

        # Ensure images have same dimensions for comparison
        if img1_np.shape != img2_np.shape:
            # print(f"Warning: Images '{os.path.basename(img1_path)}' and '{os.path.basename(img2_path)}' have different dimensions. Cannot compare.")
            return True  # Treat as materially different if dimensions mismatch

        width, height = img1.size

        # Calculate crop box for inner rectangle
        crop_width = int(width * inner_rectangle_percentage)
        crop_height = int(height * inner_rectangle_percentage)
        left = (width - crop_width) // 2
        top = (height - crop_height) // 2
        right = left + crop_width
        bottom = top + crop_height
        crop_box = (left, top, right, bottom)

        # Handle case where cropping results in zero dimensions
        if crop_width <= 0 or crop_height <= 0:
            # print(f"Warning: Cropped region has zero dimensions for '{os.path.basename(img1_path)}'. Treating as materially different.")
            return True  # Cannot compare if crop area is invalid

        img1_cropped_np = img1_np[top:bottom, left:right]
        img2_cropped_np = img2_np[top:bottom, left:right]

        # Calculate SSIM
        similarity_index = ssim(img1_cropped_np, img2_cropped_np, data_range=255)  # Assuming 8-bit grayscale (0-255)

        print(
            f"Comparing '{os.path.basename(img1_path)}' and '{os.path.basename(img2_path)}': SSIM = {similarity_index:.4f}")

        # If SSIM is below the threshold, they are considered materially different
        if similarity_index < ssim_similarity_threshold:
            return True  # Material difference detected
        else:
            return False  # No material difference (considered duplicate)

    except Exception as e:
        print(f"Error comparing images '{os.path.basename(img1_path)}' and '{os.path.basename(img2_path)}': {e}")
        return True  # Default to material difference if error occurs


def run_duplicate_detection(folder_to_check, start_filename_for_dup_check, inner_rect_percent, ssim_similarity_threshold):
    """
    Runs duplicate detection on files within a specified folder.
    Compares files sequentially, marking a chain of duplicates in one pass.
    """
    print(f"\n--- Running Duplicate Detection in '{folder_to_check}' ---")

    image_extensions = (".jpg", ".jpeg", ".png")
    all_image_files_in_folder = sorted([f for f in os.listdir(folder_to_check)
                                        if f.lower().endswith(image_extensions)
                                        and os.path.isfile(os.path.join(folder_to_check, f))])

    # Filter files that are greater than or equal to the start_filename and not already DUP
    relevant_files_for_dup_check = []
    found_start_file = False
    if start_filename_for_dup_check is None: # Treat None as an empty string for comparison logic
        start_filename_for_dup_check = ""

    for f in all_image_files_in_folder:
        if f >= start_filename_for_dup_check:
            found_start_file = True

        if found_start_file and "-DUP" not in f:
            relevant_files_for_dup_check.append(f)

    if len(relevant_files_for_dup_check) < 2:
        print(f"Not enough non-DUP relevant files for duplicate comparison in '{folder_to_check}' (starting from '{start_filename_for_dup_check}' if provided).")
        return

    # Initialize the reference file
    current_reference_file_name = relevant_files_for_dup_check[0]
    current_reference_file_path = os.path.join(folder_to_check, current_reference_file_name)

    # Start iterating from the second file
    i = 1
    while i < len(relevant_files_for_dup_check):
        next_file_name = relevant_files_for_dup_check[i]
        next_file_path = os.path.join(folder_to_check, next_file_name)

        # In case the current reference file itself was somehow marked DUP mid-run or from a prior partial run
        # This re-initializes the reference to the next non-DUP file
        if "-DUP" in current_reference_file_name or not os.path.exists(current_reference_file_path):
            new_reference_found = False
            for j in range(i, len(relevant_files_for_dup_check)):
                if "-DUP" not in relevant_files_for_dup_check[j] and \
                   os.path.exists(os.path.join(folder_to_check, relevant_files_for_dup_check[j])):
                    current_reference_file_name = relevant_files_for_dup_check[j]
                    current_reference_file_path = os.path.join(folder_to_check, current_reference_file_name)
                    i = j + 1 # Continue comparison from the file after the new reference
                    new_reference_found = True
                    break
            if not new_reference_found: # All remaining relevant files are DUPs or don't exist
                break # Exit loop
            if i >= len(relevant_files_for_dup_check): # If only reference left or no more files to compare
                break
            continue # Restart while loop with new reference

        if os.path.exists(current_reference_file_path) and os.path.exists(next_file_path):
            is_materially_different = compare_images_visually(
                current_reference_file_path,
                next_file_path,
                inner_rectangle_percentage=inner_rect_percent,
                ssim_similarity_threshold=ssim_similarity_threshold
            )

            if not is_materially_different:
                # Mark 'next_file' as a duplicate of 'current_reference_file'
                base, ext = os.path.splitext(next_file_name)
                new_next_file_name = f"{base}-DUP{ext}"
                # FIX: Correctly form new_next_file_path by joining folder_to_check with new_next_file_name
                new_next_file_path = os.path.join(folder_to_check, new_next_file_name)

                try:
                    os.rename(next_file_path, new_next_file_path)
                    print(f"Renamed '{next_file_name}' to '{new_next_file_name}' (Duplicate of '{current_reference_file_name}').")

                    # Update relevant_files_for_dup_check list in memory
                    relevant_files_for_dup_check[i] = new_next_file_name

                    i += 1 # Move to the next file, still comparing against the SAME current_reference_file
                except OSError as e:
                    print(f"Error renaming '{next_file_name}': {e}")
                    i += 1 # Move on even if rename fails
            else:
                # Material difference found! The 'next_file' becomes the new reference.
                print(f"'{next_file_name}' is materially different from '{current_reference_file_name}'. Setting as new reference.")
                current_reference_file_name = next_file_name
                current_reference_file_path = os.path.join(folder_to_check, current_reference_file_name)
                i += 1 # Move to the next file to compare against the NEW reference
        else:
            print(f"Warning: One or both files for comparison not found: '{current_file_name}', '{next_file_name}'. Skipping.") # This line needs to be current_reference_file_name
            i += 1

    print("\n--- Duplicate detection complete ---")

def main():
    parser = argparse.ArgumentParser(description="Detect duplicate image files in a folder using SSIM.")
    parser.add_argument("--path", type=str, default=".",
                        help="Path to the folder containing image files (default: current directory).")
    parser.add_argument("--filename", type=str, default=None,
                        help="Start processing from this filename (lexical order). If not provided, starts from the first relevant file.")
    parser.add_argument("--inner_rect_percent", type=float, default=0.90,
                        help="Percentage of the inner rectangle to use for comparison (e.g., 0.90 for 90%%).")
    parser.add_argument("--ssim_threshold", type=float, default=0.95,
                        help="SSIM similarity threshold. Values below this are considered materially different (default: 0.95).")
    args = parser.parse_args()

    folder_path = os.path.abspath(args.path)
    if not os.path.isdir(folder_path):
        print(f"Error: Path '{folder_path}' is not a valid directory.")
        return

    print(f"\n--- Starting duplicate detection in '{folder_path}' ---")
    print(
        f"Parameters: Start Filename='{args.filename}', Inner Rectangle %={args.inner_rect_percent * 100}%, SSIM Threshold={args.ssim_threshold}")

    # Pass the arguments directly to run_duplicate_detection
    run_duplicate_detection(
        folder_to_check=folder_path,
        start_filename_for_dup_check=args.filename if args.filename else "",  # Empty string for all files
        inner_rect_percent=args.inner_rect_percent,
        ssim_similarity_threshold=args.ssim_threshold
    )


if __name__ == "__main__":
    main()