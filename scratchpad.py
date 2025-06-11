import os
from PIL import Image, ImageChops
import numpy as np
import shutil  # For creating directory safely
from skimage.metrics import structural_similarity as ssim


def split_image_horizontally(image_path, left_output_folder, right_output_folder, split_width=1920):
    """
    Splits an image horizontally at a specified width.
    Saves the left part to left_output_folder and right part to right_output_folder.
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

    except Exception as e:
        print(f"Error splitting image '{os.path.basename(image_path)}': {e}")


def compare_images_visually(img1_path, img2_path, inner_rectangle_percentage=0.9, material_difference_threshold=0.1):
    """
    Compares the inner rectangle (e.g., 90%) of two images visually.
    Returns True if there's a material difference, False otherwise.
    The comparison uses mean absolute difference of pixel values within the cropped regions.
    """
    try:
        img1 = Image.open(img1_path).convert("L")  # Ensure grayscale
        img2 = Image.open(img2_path).convert("L")

        # Convert PIL Image to NumPy array for scikit-image
        img1_np = np.array(img1)
        img2_np = np.array(img2)

        # Ensure images have same dimensions for comparison (already handled, but crucial for SSIM)
        if img1_np.shape != img2_np.shape:
            print(
                f"Warning: Images '{os.path.basename(img1_path)}' and '{os.path.basename(img2_path)}' have different dimensions. Cannot compare.")
            return True  # Treat as materially different

        # Calculate crop box for inner rectangle (same as before)
        width, height = img1.size
        crop_width = int(width * inner_rectangle_percentage)
        crop_height = int(height * inner_rectangle_percentage)
        left = (width - crop_width) // 2
        top = (height - crop_height) // 2
        right = left + crop_width
        bottom = top + crop_height
        crop_box = (left, top, right, bottom)

        # Crop NumPy arrays directly
        img1_cropped_np = img1_np[top:bottom, left:right]
        img2_cropped_np = img2_np[top:bottom, left:right]

        # Calculate SSIM
        # You might need to adjust data_range based on your pixel values (0-255 for grayscale)
        similarity_index = ssim(img1_cropped_np, img2_cropped_np,
                                data_range=img1_cropped_np.max() - img1_cropped_np.min())

        # SSIM returns 1 for identical images, 0 for no similarity, negative for anti-correlation.
        # So, a lower SSIM means more difference.
        # We want a high SSIM to be considered "not materially different" (duplicate).
        # Therefore, your threshold logic would be: if similarity_index < SSIM_THRESHOLD, then materially different.

        print(
            f"Comparing '{os.path.basename(img1_path)}' and '{os.path.basename(img2_path)}': SSIM = {similarity_index:.4f}")

        # Example threshold: If SSIM is below 0.9 (meaning more than 10% difference in structure/luminance/contrast)
        SSIM_THRESHOLD = 0.95  # You will need to tune this value!

        if similarity_index < SSIM_THRESHOLD:
            return True  # Material difference detected
        else:
            return False  # No material difference (considered duplicate)
    except Exception as e:
        print(f"Error comparing images '{os.path.basename(img1_path)}' and '{os.path.basename(img2_path)}': {e}")
        return True  # Default to material difference if error occurs


def run_duplicate_detection(folder_to_check, start_filename_for_dup_check, inner_rect_percent, material_diff_thresh):
    """
    Runs duplicate detection on files within a specified folder.
    Compares files sequentially, marking a chain of duplicates in one pass.
    """
    print(f"\n--- Running Duplicate Detection in '{folder_to_check}' ---")

    all_jpg_files = sorted([f for f in os.listdir(folder_to_check) if
                            f.lower().endswith(".jpg") and os.path.isfile(os.path.join(folder_to_check, f))])

    # Filter files that are greater than or equal to the start_filename
    # This list will be modified as files are renamed, so we need to be careful
    relevant_files_for_dup_check = [f for f in all_jpg_files if f >= start_filename_for_dup_check and "-DUP" not in f]

    if len(relevant_files_for_dup_check) < 2:
        print(f"Not enough non-DUP relevant files for duplicate comparison in '{folder_to_check}'.")
        return

    # Initialize the reference file
    current_reference_file_name = relevant_files_for_dup_check[0]
    current_reference_file_path = os.path.join(folder_to_check, current_reference_file_name)

    # Start iterating from the second file
    i = 1
    while i < len(relevant_files_for_dup_check):
        next_file_name = relevant_files_for_dup_check[i]
        next_file_path = os.path.join(folder_to_check, next_file_name)

        # Skip if the current reference file itself was somehow already marked DUP (e.g., from a prior partial run)
        if "-DUP" in current_reference_file_name:
            # Find the next non-DUP file to be the new reference
            new_reference_found = False
            for j in range(i, len(relevant_files_for_dup_check)):
                if "-DUP" not in relevant_files_for_dup_check[j]:
                    current_reference_file_name = relevant_files_for_dup_check[j]
                    current_reference_file_path = os.path.join(folder_to_check, current_reference_file_name)
                    i = j + 1  # Continue comparison from the file after the new reference
                    new_reference_found = True
                    break
            if not new_reference_found:  # All remaining files are DUPs
                break  # Exit loop
            continue  # Restart while loop with new reference

        if os.path.exists(current_reference_file_path) and os.path.exists(next_file_path):
            is_materially_different = compare_images_visually(
                current_reference_file_path,
                next_file_path,
                inner_rectangle_percentage=inner_rect_percent,
                material_difference_threshold=material_diff_thresh
            )

            if not is_materially_different:
                # Mark 'next_file' as a duplicate of 'current_reference_file'
                base, ext = os.path.splitext(next_file_name)
                new_next_file_name = f"{base}-DUP{ext}"
                new_next_file_path = os.path.join(folder_to_check, new_next_file_name)

                try:
                    os.rename(next_file_path, new_next_file_path)
                    print(
                        f"Renamed '{next_file_name}' to '{new_next_file_name}' (Duplicate of '{current_reference_file_name}').")

                    # Update relevant_files_for_dup_check list *in memory*
                    # so that subsequent comparisons don't try to use the old name
                    # and the DUP-marked file isn't picked as a new reference.
                    # This is crucial for correct chaining.
                    relevant_files_for_dup_check[i] = new_next_file_name

                    i += 1  # Move to the next file, still comparing against the SAME current_reference_file
                except OSError as e:
                    print(f"Error renaming '{next_file_name}': {e}")
                    i += 1  # Move on even if rename fails
            else:
                # Material difference found! The 'next_file' becomes the new reference.
                print(
                    f"'{next_file_name}' is materially different from '{current_reference_file_name}'. Setting as new reference.")
                current_reference_file_name = next_file_name
                current_reference_file_path = os.path.join(folder_to_check, current_reference_file_name)
                i += 1  # Move to the next file to compare against the NEW reference
        else:
            print(
                f"Warning: One or both files for comparison not found: '{current_reference_file_name}', '{next_file_name}'. Skipping.")
            i += 1


def process_images_in_folder(start_filename, folder_path, split_width=1920, inner_rect_percent=0.9,
                             material_diff_thresh=0.1):
    """
    Main function to process images in a folder based on the specified order:
    1. Split files into separate left/right subfolders.
    2. Detect duplicates within the left_splits folder.
    3. Detect duplicates within the right_splits folder.
    """
    print(f"\n--- Starting image processing in '{folder_path}' ---")
    print(
        f"Parameters: Start Filename='{start_filename}', Split Width={split_width}, Inner Rectangle %={inner_rect_percent * 100}%, Material Diff Threshold={material_diff_thresh}")

    # Create subfolders for split images
    left_splits_folder = os.path.join(folder_path, "_left_splits")
    right_splits_folder = os.path.join(folder_path, "_right_splits")
    os.makedirs(left_splits_folder, exist_ok=True)
    os.makedirs(right_splits_folder, exist_ok=True)
    print(f"Left split images will be saved to: '{left_splits_folder}'")
    print(f"Right split images will be saved to: '{right_splits_folder}'")

    all_original_jpg_files = sorted([f for f in os.listdir(folder_path) if
                                     f.lower().endswith(".jpg") and os.path.isfile(os.path.join(folder_path, f))])

    # Filter files that are greater than or equal to the start_filename
    relevant_files_for_splitting = [f for f in all_original_jpg_files if f >= start_filename]

    if not relevant_files_for_splitting:
        print(f"No .jpg files found greater than or equal to '{start_filename}' in '{folder_path}' for splitting.")
        return

    print(f"\n--- Running Function 1: Horizontal Splits for relevant original files ---")
    for filename in relevant_files_for_splitting:
        full_path = os.path.join(folder_path, filename)
        # Ensure we don't try to split files already marked as DUP if previous runs left them
        if "-DUP" not in filename:
            split_image_horizontally(full_path, left_splits_folder, right_splits_folder, split_width)
        else:
            print(f"Skipping splitting for '{filename}' as it is already marked as DUP.")

    # --- Running Function 2: Duplicate Detection in split folders ---
    # The start_filename for duplicate detection in these folders needs to be adjusted
    # to account for the '-L' or '-R' suffix if the originals were also subject to this start_filename.
    # The `run_duplicate_detection` function sorts the files in the target folder,
    # so as long as the original file sorting works for the split files (e.g. `file-L.jpg` will come before `file-R.jpg` and `file2-L.jpg`), it will work.
    # The current logic will pick the *first* non-DUP file in the sorted list as the initial reference.

    print(f"\n--- Starting duplicate detection for '_left_splits' folder ---")
    run_duplicate_detection(
        folder_to_check=left_splits_folder,
        start_filename_for_dup_check="",
        # Empty string means check all files in the folder (as they are newly created or already filtered by prev runs)
        inner_rect_percent=inner_rect_percent,
        material_diff_thresh=material_diff_thresh
    )

    print(f"\n--- Starting duplicate detection for '_right_splits' folder ---")
    run_duplicate_detection(
        folder_to_check=right_splits_folder,
        start_filename_for_dup_check="",  # Empty string means check all files in the folder
        inner_rect_percent=inner_rect_percent,
        material_diff_thresh=material_diff_thresh
    )

    print("\n--- Image processing complete ---")


# --- How to run the script ---
if __name__ == "__main__":
    # Define your parameters
    # IMPORTANT: Adjust these parameters as needed!
    TARGET_FOLDER = "c:\\temp"  # Your specified folder
    START_FILENAME = "2025-06-03-09_06_21-001.jpg"  # Your specified starting filename
    SPLIT_AT_WIDTH = 1920
    INNER_RECTANGLE_PERCENTAGE = 0.90  # 90%
    MATERIAL_DIFFERENCE_THRESHOLD = 0.05  # Adjust this (0.0 to 1.0). Lower means more sensitive (more likely to be considered different).

    # Call the main processing function
    process_images_in_folder(
        start_filename=START_FILENAME,
        folder_path=TARGET_FOLDER,
        split_width=SPLIT_AT_WIDTH,
        inner_rect_percent=INNER_RECTANGLE_PERCENTAGE,
        material_diff_thresh=MATERIAL_DIFFERENCE_THRESHOLD
    )