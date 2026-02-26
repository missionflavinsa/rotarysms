from src.views.admin_results import process_profile_photo_original, get_original_shape_mask
import fitz

mask_res = get_original_shape_mask(205, 274)
if mask_res:
    mask_img, rect = mask_res
    print("Found Mask Target Rect:", rect)
else:
    print("Mask Res failed")
