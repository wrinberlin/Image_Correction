# -*- coding: utf-8 -*-
"""
Created on Sat Feb 21 13:18:11 2026

@author: Wolfgang Reuter
"""

from PIL import Image, ImageDraw, ImageFont
import os
import io 
import numpy as np 
from skimage.transform import  ProjectiveTransform, warp
import streamlit as st

@st.cache_data
def resize_image(image_bytes, max_size):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    resized_img, resized, scale_factor = resize_if_needed(image, max_size)
    return resized_img, resized, scale_factor 

@st.cache_data
def transform_image(image, degrees, warp_offsets):
    img = rotate(image, degrees).convert("RGBA")
    img_array = np.array(img)
    h, w = img_array.shape[:2]

    src = np.array([[0, 0], [w, 0], [w, h], [0, h]])

    dst = np.array([
        [warp_offsets["tl_x"] * w, warp_offsets["tl_y"] * h],
        [w + warp_offsets["tr_x"] * w, warp_offsets["tr_y"] * h],
        [w + warp_offsets["br_x"] * w, h + warp_offsets["br_y"] * h],
        [warp_offsets["bl_x"] * w, h + warp_offsets["bl_y"] * h]
    ])

    transform = ProjectiveTransform()
    transform.estimate(dst, src)

    warped = warp(
        img_array,
        transform,
        output_shape=(h, w),
        preserve_range=True
    )

    warped = warped.astype(np.uint8)
    result = Image.fromarray(warped, mode="RGBA")

    return result


@st.cache_data
def apply_watermark_permanent(warped_image, watermark_text):
    if watermark_text:
        return add_watermark_to_image(warped_image.copy(), watermark_text)
    return warped_image

def resize_if_needed(image, max_size):
    original_width, original_height = image.size
    
    if original_width > max_size or original_height > max_size:
        # Calculate scale factor
        scale_factor = min(
            max_size / original_width,
            max_size / original_height
        )
        
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        
        resized_image = image.resize((new_width, new_height))
        
        return resized_image, True, scale_factor
    
    # No resizing needed
    return image, False, 1.0

def rotate(image: Image.Image, degrees: float):
    """
    Rotates a PIL image by given degrees.

    Parameters:
    - image (PIL.Image): Input image
    - degrees (float): Rotation angle

    Returns:
    - PIL.Image: Rotated image
    """
    return image.rotate(degrees, expand=True)


def add_watermark_to_image(image, watermark_text):
    image = image.convert("RGBA")
    
    # Try to load a TTF font, fallback to default if not found
    font_path = os.path.join("fonts", "DejaVuSans.ttf")
    diagonal = (image.size[0]**2 + image.size[1]**2)**0.5
    font_size = int(diagonal / 12)
    font = ImageFont.truetype(font_path, font_size)
    
    watermark_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(watermark_layer)
    
    # Use textbbox instead of textsize
    bbox = draw.textbbox((0, 0), watermark_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (image.width - text_width) / 2
    y = (image.height - text_height) / 2
    
    # Draw diagonal watermark
    temp_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
    temp_draw = ImageDraw.Draw(temp_layer)
    temp_draw.text((x, y), watermark_text, fill=(255, 255, 255, 50), font=font)
    temp_layer = temp_layer.rotate(45, resample=Image.BICUBIC, center=(image.width/2, image.height/2))
    
    combined = Image.alpha_composite(image, temp_layer)
    return combined

def prepare_orig_image():
    # Make a copy of the original full-res image
    orig_img = st.session_state.orig_image.copy()

    # ---------------------
    # Apply rotation
    # ---------------------
    if st.session_state.degrees != 0:
        orig_img = rotate(orig_img, st.session_state.degrees).convert("RGBA")

    # ---------------------
    # Apply trapezoidal warp
    # ---------------------
    img_array = np.array(orig_img)
    h, w = img_array.shape[:2]
    scale_w = w / st.session_state.image.width
    scale_h = h / st.session_state.image.height

    src = np.array([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.array([
        [
            st.session_state.warp_tl_x_offset * st.session_state.image.width * scale_w,
            st.session_state.warp_tl_y_offset * st.session_state.image.height * scale_h,
        ],
        [
            w + st.session_state.warp_tr_x_offset * st.session_state.image.width * scale_w,
            st.session_state.warp_tr_y_offset * st.session_state.image.height * scale_h,
        ],
        [
            w + st.session_state.warp_br_x_offset * st.session_state.image.width * scale_w,
            h + st.session_state.warp_br_y_offset * st.session_state.image.height * scale_h,
        ],
        [
            st.session_state.warp_bl_x_offset * st.session_state.image.width * scale_w,
            h + st.session_state.warp_bl_y_offset * st.session_state.image.height * scale_h,
        ],
    ])

    transform = ProjectiveTransform()
    transform.estimate(dst, src)
    warped = warp(img_array, transform, output_shape=(h, w))
    orig_img = Image.fromarray((warped * 255).astype(np.uint8))

    # ---------------------
    # Cut to rectangle if requested
    # ---------------------
    if st.session_state.cut_to_rect:
        left = st.session_state.rect_left_width_margin * scale_w
        top = st.session_state.rect_top_height_margin * scale_h
        right = orig_img.width - st.session_state.rect_right_width_margin * scale_w
        bottom = orig_img.height - st.session_state.rect_bottom_height_margin * scale_h

        left = max(0, left)
        top = max(0, top)
        right = min(orig_img.width, right)
        bottom = min(orig_img.height, bottom)

        if right > left and bottom > top:
            orig_img = orig_img.crop((left, top, right, bottom))

    # ---------------------
    # Apply watermark if enabled
    # ---------------------
    
    if st.session_state.watermark_enabled:
        orig_img = add_watermark_to_image(orig_img, st.session_state.watermark_text)
    
    img_bytes = io.BytesIO()
    orig_img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    st.session_state.original_image_bytes = img_bytes

    st.success("Original image (altered) is ready for download!")
    
    return orig_img, img_bytes
    
    


how_to_use_text = """
This app allows you to correct images if they are turned, warped - or have 
rims that you want to remove. 

1. Upload an image from you file system (Browse files). If the width or height exceeds 1000 pixels, the image is resized for performance reasons. But don't worry, all you alterations will be transfered to your original image, if you wish. Just press "Prepare Original Image (Altered)" once you are finished. This might take a few seconds. Wait until the notice "Original image (altered) is ready for download!" comes up and then press "Download Original Image (Altered)".
2. Once an image is uploaded, a control panel will appear on the left side of the screen. Use the buttons there to rotate or warp the image. Every alteration can be undone.  
3. Press "Show rectangle" to have a better reference frame for you alterations. You can also cut the image to the size of the rectangle at the end by pressing the button "Cut to Rectangle".
3. Add a watermark if desired by pressing "Add Watermark". You can choose your own text. 
5. Download your corrected image at the end. 
"""
