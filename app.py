# -*- coding: utf-8 -*-
"""
Created on Sat Feb 21 13:06:28 2026

@author: Wolfgang Reuter

TODO: Refactor properly
TODO: Add button for manual changes of parameters 
TDOO: Add brightness change

Usage: 
    1) cd to directory 
    2) In an anaconda shell, type streamlit run app.py
"""

import streamlit as st
from PIL import Image, ImageDraw
from utils import rotate
import io
import numpy as np
from skimage.transform import ProjectiveTransform, warp

from utils import resize_image, add_watermark_to_image, how_to_use_text, \
    transform_image

st.set_page_config(page_title="Image Rotator + Warp + Rectangle", layout="wide")
st.title("Image Correction")

# =============================================================================
# Constants
# =============================================================================

MAX_SIZE = 1000
RECT_BORDER_WIDTH = 4

# ---------------------
# Session State Defaults
# ---------------------

defaults = {
    "show_help": True,
    "image": None,
    "orig_image": None,
    "resized": False,
    "scale_factor": 1.0,
    "show_resize_toast": False,
    "cut_image": None,
    "show_rectangle": False,
    "rect_left_width_margin": 10,
    "rect_right_width_margin": 10,
    "rect_top_height_margin": 10,
    "rect_bottom_height_margin": 10,
    "rect_increment": 5,
    "degrees": 0,
    "warp_tl_x_offset": 0.0,
    "warp_tl_y_offset": 0.0,
    "warp_tr_x_offset": 0.0,
    "warp_tr_y_offset": 0.0,
    "warp_bl_x_offset": 0.0,
    "warp_bl_y_offset": 0.0,
    "warp_br_x_offset": 0.0,
    "warp_br_y_offset": 0.0,
    "watermark_enabled": False, 
    "show_watermark_input": False,
    "watermark_text": "© ", 
    "watermark_text_orig": "",
    "cut_to_rect": False,
}

# =============================================================================
# Functions 
# =============================================================================

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
    
# =============================================================================
# Set up defaults - and help message 
# =============================================================================

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value 

if st.session_state.show_help: 
    with st.expander("How to use the app", expanded=False):
        st.write(how_to_use_text)

if st.session_state.show_help: 
    if st.button("Do not show again"): 
        st.session_state.show_help = False
        st.rerun()

# ---------------------
# Upload Image
# ---------------------

uploaded_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGBA")
    resized_img, resized, scale_factor = resize_image(uploaded_file.getvalue(), MAX_SIZE)

    st.session_state.image = resized_img if resized else image
    st.session_state.orig_image = image
    st.session_state.resized = resized
    st.session_state.scale_factor = scale_factor
    
    st.session_state.show_resize_toast = resized

    if resized:
        image_width, image_height = st.session_state.image.size
        st.session_state.rect_increment = int(max(image_width, image_height) * 0.005)
    # Optionally store the raw bytes if needed for download
    st.session_state.image_bytes = uploaded_file.getvalue()

if st.session_state.show_resize_toast:
    st.info("Image was resized to improve performance. If you wish, all your alterations can at the end be applied to the original image, which you can then download. ", icon="ℹ️")
    # st.session_state.show_resize_toast = False  # 👈 Reset flag

# ---------------------
# Layout: Controls Left, Image Right
# ---------------------
if st.session_state.image:
    control_col, image_col = st.columns([1, 1])

    # ---------------------
    # Control Panel (left column)
    # ---------------------
    with control_col:
        st.subheader("Rectangle Controls")
        rect_col1, rect_col2 = st.columns(2)
        with rect_col1:
            if st.button("🟥 Show Rectangle"):
                st.session_state.show_rectangle = True
        with rect_col2:
            if st.button("❌ Hide Rectangle"):
                st.session_state.show_rectangle = False 
                st.session_state.cut_to_rect = False

        st.write("**Rectangle Size**")
        size_col1, size_col2, size_col3, size_col4, size_col5, size_col6, size_col7, size_col8 = st.columns(8)
        with size_col1:
            if st.button("| ▶"): st.session_state.rect_left_width_margin += st.session_state.rect_increment
        with size_col2:
            if st.button("| ◀"): st.session_state.rect_left_width_margin -= st.session_state.rect_increment
        with size_col3:
            if st.button("▶ |"): st.session_state.rect_right_width_margin -= st.session_state.rect_increment
        with size_col4:
            if st.button("◀ |"): st.session_state.rect_right_width_margin += st.session_state.rect_increment
        with size_col5:
            if st.button("‾ ▼"): st.session_state.rect_top_height_margin += st.session_state.rect_increment
        with size_col6:
            if st.button("‾ ▲"): st.session_state.rect_top_height_margin -= st.session_state.rect_increment
        with size_col7:
            if st.button("_ ▼"): st.session_state.rect_bottom_height_margin -= st.session_state.rect_increment
        with size_col8:
            if st.button("_ ▲"): st.session_state.rect_bottom_height_margin += st.session_state.rect_increment

        st.subheader("Rotation Controls")
        rot_col1, rot_col2, rot_col3, rot_col4 = st.columns(4)
        with rot_col1:
            if st.button("↻ +1°"):
                st.session_state.degrees -= 1
        with rot_col2:
            if st.button("↺ -1°"):
                st.session_state.degrees += 1
        with rot_col3:
            if st.button("↻ +0.25°"):
                st.session_state.degrees -= 0.25
        with rot_col4:
            if st.button("↺ -0.25°"):
                st.session_state.degrees += 0.25

        st.subheader("Warp Controls Top Left")
        
        warp_tl_col1, warp_tl_col2, warp_tl_col3, warp_tl_col4 = st.columns(4)

        with warp_tl_col1:
            if st.button("Top-Left ◀"):
                st.session_state.warp_tl_x_offset -= 0.01
        
        with warp_tl_col2:
            if st.button("Top-Left ▶"):
                st.session_state.warp_tl_x_offset += 0.01
        
        with warp_tl_col3:
            if st.button("Top-Left ▲"):
                st.session_state.warp_tl_y_offset -= 0.01
        
        with warp_tl_col4:
            if st.button("Top-Left ▼"):
                st.session_state.warp_tl_y_offset += 0.01
                
        st.caption(f"X: {st.session_state.warp_tl_x_offset:.2f} | Y: {st.session_state.warp_tl_y_offset:.2f}")
        
        st.subheader("Warp Controls Top Right")
        
        warp_tr_col1, warp_tr_col2, warp_tr_col3, warp_tr_col4 = st.columns(4)

        with warp_tr_col1:
            if st.button("Top-Right ◀"):
                st.session_state.warp_tr_x_offset -= 0.01
        
        with warp_tr_col2:
            if st.button("Top-Right ▶"):
                st.session_state.warp_tr_x_offset += 0.01
        
        with warp_tr_col3:
            if st.button("Top-Right ▲"):
                st.session_state.warp_tr_y_offset -= 0.01
        
        with warp_tr_col4:
            if st.button("Top-Right ▼"):
                st.session_state.warp_tr_y_offset += 0.01
                
        st.caption(f"X: {st.session_state.warp_tr_x_offset:.2f} | Y: {st.session_state.warp_tr_y_offset:.2f}")

        st.subheader("Warp Controls Bottom Left")
        
        warp_bl_col1, warp_bl_col2, warp_bl_col3, warp_bl_col4 = st.columns(4)

        with warp_bl_col1:
            if st.button("Bottom-Left ◀"):
                st.session_state.warp_bl_x_offset -= 0.01
        
        with warp_bl_col2:
            if st.button("Bottom-Left ▶"):
                st.session_state.warp_bl_x_offset += 0.01
        
        with warp_bl_col3:
            if st.button("Bottom-Left ▲"):
                st.session_state.warp_bl_y_offset -= 0.01
        
        with warp_bl_col4:
            if st.button("Bottom-Left ▼"):
                st.session_state.warp_bl_y_offset += 0.01
                
        st.caption(f"X: {st.session_state.warp_bl_x_offset:.2f} | Y: {st.session_state.warp_bl_y_offset:.2f}")

        
        st.subheader("Warp Controls Bottom Right")
        
        warp_br_col1, warp_br_col2, warp_br_col3, warp_br_col4 = st.columns(4)

        with warp_br_col1:
            if st.button("Bottom-Right ◀"):
                st.session_state.warp_br_x_offset -= 0.01
        
        with warp_br_col2:
            if st.button("Bottom-Right ▶"):
                st.session_state.warp_br_x_offset += 0.01
        
        with warp_br_col3:
            if st.button("Bottom-Right ▲"):
                st.session_state.warp_br_y_offset -= 0.01
        
        with warp_br_col4:
            if st.button("Bottom-Right ▼"):
                st.session_state.warp_br_y_offset += 0.01
                
        st.caption(f"X: {st.session_state.warp_br_x_offset:.2f} | Y: {st.session_state.warp_br_y_offset:.2f}")

    # ---------------------
    # Watermark Controls
    # ---------------------
    
    # Toggle watermark mode
    if st.button("Remove Watermark" if st.session_state.watermark_enabled else "Add Watermark"):
        st.session_state.watermark_enabled = not st.session_state.watermark_enabled
        st.session_state.show_watermark_input = st.session_state.watermark_enabled
        if not st.session_state.watermark_enabled:
            # Reset to clean image
            st.session_state.image = st.session_state.image.copy()
            st.session_state.watermark_text_orig = ""
            st.rerun()
    
    # Show input if watermarking is active
    if st.session_state.show_watermark_input:
        st.session_state.watermark_text = st.text_input(
            "Watermark text:",
            value=st.session_state.watermark_text
        )
    
    # Apply watermark button (top-level)
    if st.session_state.show_watermark_input and st.button("Apply Watermark"):
        
        st.session_state.watermark_enabled = True
        st.session_state.show_watermark_input = False  # hide input & button after apply
        st.rerun()

    # ---------------------
    # Image Processing
    # ---------------------
    # Start from original image
    
    warp_offsets = {
        "tl_x": st.session_state.warp_tl_x_offset,
        "tl_y": st.session_state.warp_tl_y_offset,
        "tr_x": st.session_state.warp_tr_x_offset,
        "tr_y": st.session_state.warp_tr_y_offset,
        "bl_x": st.session_state.warp_bl_x_offset,
        "bl_y": st.session_state.warp_bl_y_offset,
        "br_x": st.session_state.warp_br_x_offset,
        "br_y": st.session_state.warp_br_y_offset,
    }
    
    # Start from the watermarked image
    warped_image = transform_image(
        st.session_state.image,
        st.session_state.degrees,
        warp_offsets
    )
    
    if st.session_state.watermark_enabled: 
        warped_image = add_watermark_to_image(
            warped_image,
            st.session_state.watermark_text
        )
    
    # Draw rectangle (optional)
    if st.session_state.show_rectangle:
        draw = ImageDraw.Draw(warped_image)
        draw.rectangle(
            [
                st.session_state.rect_left_width_margin,
                st.session_state.rect_top_height_margin,
                warped_image.width - st.session_state.rect_right_width_margin,
                warped_image.height - st.session_state.rect_bottom_height_margin
            ],
            outline="red",
            width=RECT_BORDER_WIDTH
        )
    
    # Crop to rectangle if requested
    if st.button("Cut to Rectangle"):
        left = st.session_state.rect_left_width_margin + RECT_BORDER_WIDTH
        top = st.session_state.rect_top_height_margin + RECT_BORDER_WIDTH
        right = warped_image.width - st.session_state.rect_right_width_margin - RECT_BORDER_WIDTH
        bottom = warped_image.height - st.session_state.rect_bottom_height_margin - RECT_BORDER_WIDTH
        
        left = max(0, left)
        top = max(0, top)
        right = min(warped_image.width, right)
        bottom = min(warped_image.height, bottom)
    
        if right > left and bottom > top:
            warped_image = warped_image.crop((left, top, right, bottom))
            st.session_state.cut_image = warped_image.copy()
            st.session_state.cut_to_rect = True
    
    # ---------------------
    # Display image
    # ---------------------
    
    with image_col:
        st.image(warped_image, width=image_width)
        
    if st.session_state.cut_image != None: 
        download_image = st.session_state.cut_image.copy()
    else: 
        download_image = warped_image.copy()
    
    img_bytes = io.BytesIO()
    download_image.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    
    st.download_button(
        label="Download Image",
        data=img_bytes,
        file_name="processed_image.png",
        mime="image/png"
    )
    
    # ---------------------
    # Download Original Image (Altered)
    # ---------------------
    
    # Button to trigger heavy processing
    if st.session_state.resized:
        if st.button("Prepare Original Image (Altered)"):
            with st.spinner("Preparing image for download..."):
            
                prepare_orig_image()
    
            # ---------------------
            # Show download button only if processed
            # ---------------------
            if "original_image_bytes" in st.session_state:
                st.download_button(
                    label="Download Original Image (Altered)",
                    data=st.session_state.original_image_bytes,
                    file_name="original_image_altered.png",
                    mime="image/png"
                )
