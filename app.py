# -*- coding: utf-8 -*-
"""
Created on Sat Feb 21 13:06:28 2026

@author: Wolfgang Reuter

Usage: 
    1) cd to directory 
    2) In an anaconda shell, type streamlit run app.py
"""
import streamlit as st
from PIL import Image, ImageDraw
from utils import rotate
import io
import numpy as np
import hashlib
from skimage.transform import ProjectiveTransform, warp

from utils import add_watermark_to_image

st.set_page_config(page_title="Image Rotator + Warp + Rectangle", layout="wide")
st.title("Image Upload, Rotate, Warp & Reference Rectangle")

# ---------------------
# Session State Defaults
# ---------------------

defaults = {
    "degrees": 0,
    "image": None,
    "rotated_image": None,
    "show_rectangle": False,
    "rect_left_width_margin": 10,
    "rect_right_width_margin": 10,
    "rect_top_height_margin": 10,
    "rect_bottom_height_margin": 10,
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
    "cut_to_rect": False,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ---------------------
# Upload Image
# ---------------------

uploaded_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"])

def reset_image_state():
    for key, value in defaults.items():
        st.session_state[key] = value

if uploaded_file is not None:

    file_bytes = uploaded_file.getvalue()
    file_hash = hashlib.md5(file_bytes).hexdigest()

    if "last_file_hash" not in st.session_state:
        st.session_state.last_file_hash = None

    if file_hash != st.session_state.last_file_hash:
        st.session_state.last_file_hash = file_hash
        reset_image_state()

    # IMPORTANT: store image in session state
    st.session_state.image = Image.open(uploaded_file)

# Later in your app:
if st.session_state.image is not None:
    image = st.session_state.image

# ---------------------
# Layout: Controls Left, Image Right
# ---------------------
if st.session_state.image:
    control_col, image_col = st.columns([3, 4])

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
            if st.button("| ➡️"): st.session_state.rect_left_width_margin += 5
        with size_col2:
            if st.button("| ⬅️"): st.session_state.rect_left_width_margin -= 5
        with size_col3:
            if st.button("➡️ |"): st.session_state.rect_right_width_margin -= 5
        with size_col4:
            if st.button("⬅️ |"): st.session_state.rect_right_width_margin += 5
        with size_col5:
            if st.button("‾‾⬇️"): st.session_state.rect_top_height_margin += 5
        with size_col6:
            if st.button("‾‾⬆️"): st.session_state.rect_top_height_margin -= 5
        with size_col7:
            if st.button("__⬇️"): st.session_state.rect_bottom_height_margin -= 5
        with size_col8:
            if st.button("__⬆️"): st.session_state.rect_bottom_height_margin += 5

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
            if st.button("Top-Left ⬅"):
                st.session_state.warp_tl_x_offset -= 0.01
        
        with warp_tl_col2:
            if st.button("Top-Left ➡"):
                st.session_state.warp_tl_x_offset += 0.01
        
        with warp_tl_col3:
            if st.button("Top-Left ⬆"):
                st.session_state.warp_tl_y_offset -= 0.01
        
        with warp_tl_col4:
            if st.button("Top-Left ⬇"):
                st.session_state.warp_tl_y_offset += 0.01
                
        st.caption(f"X: {st.session_state.warp_tl_x_offset:.2f} | Y: {st.session_state.warp_tl_y_offset:.2f}")
        
        st.subheader("Warp Controls Top Right")
        
        warp_tr_col1, warp_tr_col2, warp_tr_col3, warp_tr_col4 = st.columns(4)

        with warp_tr_col1:
            if st.button("Top-Right ⬅"):
                st.session_state.warp_tr_x_offset -= 0.01
        
        with warp_tr_col2:
            if st.button("Top-Right ➡"):
                st.session_state.warp_tr_x_offset += 0.01
        
        with warp_tr_col3:
            if st.button("Top-Right ⬆"):
                st.session_state.warp_tr_y_offset -= 0.01
        
        with warp_tr_col4:
            if st.button("Top-Right ⬇"):
                st.session_state.warp_tr_y_offset += 0.01
                
        st.caption(f"X: {st.session_state.warp_tr_x_offset:.2f} | Y: {st.session_state.warp_tr_y_offset:.2f}")

        st.subheader("Warp Controls Bottom Left")
        
        warp_bl_col1, warp_bl_col2, warp_bl_col3, warp_bl_col4 = st.columns(4)

        with warp_bl_col1:
            if st.button("Bottom-Left ⬅"):
                st.session_state.warp_bl_x_offset -= 0.01
        
        with warp_bl_col2:
            if st.button("Bottom-Left ➡"):
                st.session_state.warp_bl_x_offset += 0.01
        
        with warp_bl_col3:
            if st.button("Bottom-Left ⬆"):
                st.session_state.warp_bl_y_offset -= 0.01
        
        with warp_bl_col4:
            if st.button("Bottom-Left ⬇"):
                st.session_state.warp_bl_y_offset += 0.01
                
        st.caption(f"X: {st.session_state.warp_bl_x_offset:.2f} | Y: {st.session_state.warp_bl_y_offset:.2f}")

        
        st.subheader("Warp Controls Bottom Right")
        
        warp_br_col1, warp_br_col2, warp_br_col3, warp_br_col4 = st.columns(4)

        with warp_br_col1:
            if st.button("Bottom-Right ⬅"):
                st.session_state.warp_br_x_offset -= 0.01
        
        with warp_br_col2:
            if st.button("Bottom-Right ➡"):
                st.session_state.warp_br_x_offset += 0.01
        
        with warp_br_col3:
            if st.button("Bottom-Right ⬆"):
                st.session_state.warp_br_y_offset -= 0.01
        
        with warp_br_col4:
            if st.button("Bottom-Right ⬇"):
                st.session_state.warp_br_y_offset += 0.01
                
        st.caption(f"X: {st.session_state.warp_br_x_offset:.2f} | Y: {st.session_state.warp_br_y_offset:.2f}")

        

    # ---------------------
    # Image Processing
    # ---------------------
    # Start from original image
    display_image = st.session_state.image.copy()
    display_image_width = display_image.size[0]

    # Apply rotation if any
    if st.session_state.degrees != 0:
        display_image = rotate(display_image, st.session_state.degrees).convert("RGBA")

    # Convert to numpy array for warping
    img_array = np.array(display_image)

    # Apply trapezoidal warp 
    h, w = img_array.shape[:2]
    src = np.array([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.array([
        [st.session_state.warp_tl_x_offset * w, st.session_state.warp_tl_y_offset * h],  # top-left moves
        [w + st.session_state.warp_tr_x_offset * w, st.session_state.warp_tr_y_offset * h],    # top-right stays
        [w + st.session_state.warp_br_x_offset * w, h + st.session_state.warp_br_y_offset * h],    # bottom-right stays
        [st.session_state.warp_bl_x_offset * w, h + st.session_state.warp_bl_y_offset * h]     # bottom-left stays
    ])
    transform = ProjectiveTransform()
    transform.estimate(dst, src)
    warped = warp(img_array, transform, output_shape=(h, w))
    warped_image = Image.fromarray((warped * 255).astype(np.uint8))

    # Draw rectangle if requested
    if st.session_state.show_rectangle:
        draw = ImageDraw.Draw(warped_image)
        draw.rectangle(
            [st.session_state.rect_left_width_margin, st.session_state.rect_top_height_margin,
             warped_image.width - st.session_state.rect_right_width_margin,
             warped_image.height - st.session_state.rect_bottom_height_margin],
            outline="red",
            width=3
        )

    # ---------------------
    # Add watermark
    # ---------------------
    
    if st.button(
        "Remove Watermark" if st.session_state.watermark_enabled else "Add Watermark"
        ):
        st.session_state.watermark_enabled = not st.session_state.watermark_enabled
        st.session_state.show_watermark_input = st.session_state.watermark_enabled
    
    if st.session_state.show_watermark_input:
        st.session_state.watermark_text = st.text_input(
            "Watermark text:",
            value=st.session_state.watermark_text
        )
    
        if st.button("Apply Watermark"):
            warped_image = add_watermark_to_image(
                warped_image,
                st.session_state.watermark_text
            )
            st.session_state.watermark_enabled = not st.session_state.watermark_enabled
            st.session_state.show_watermark_input = False 
            st.session_state.watermark_text = "© "
            
    # ---------------------
    # Cut to rectangle
    # ---------------------
    
    if st.button("Cut to Rectangle"):
        left = st.session_state.rect_left_width_margin
        top = st.session_state.rect_top_height_margin
        right = warped_image.width - st.session_state.rect_right_width_margin
        bottom = warped_image.height - st.session_state.rect_bottom_height_margin
    
        # Safety clamp (important!)
        left = max(0, left)
        top = max(0, top)
        right = min(warped_image.width, right)
        bottom = min(warped_image.height, bottom)
    
        if right > left and bottom > top:
            warped_image = warped_image.crop((left, top, right, bottom))
            st.session_state.cut_to_rect = True
        
    # ---------------------
    # Display image
    # ---------------------
    
    with image_col:
        st.image(warped_image, width=display_image_width)

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



