# -*- coding: utf-8 -*-
"""
Created on Sat Feb 21 13:18:11 2026

@author: Wolfgang Reuter
"""

from PIL import Image, ImageDraw, ImageFont
import os

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

how_to_use_text = """
This app allows you to correct images if they are turned, warped - or have 
rims that you want to remove. 

1. Upload an image from you file system (Browse files). If the width or height exceeds 1000 pixels, the image is resized for performance reasons. But don't worry, all you alterations will be transfered to your original image, if you wish. Just press "Prepare Original Image (Altered)" once you are finished. This might take a few seconds. Wait until the notice "Original image (altered) is ready for download!" comes up and then press "Download Original Image (Altered)".
2. Once an image is uploaded, a control panel will appear on the left side of the screen. Use the buttons there to rotate or warp the image. Every alteration can be undone.  
3. Press "Show rectangle" to have a better reference frame for you alterations. You can also cut the image to the size of the rectangle at the end by pressing the button "Cut to Rectangle".
3. Add a watermark if desired by pressing "Add Watermark". You can choose your own text. 
5. Download your corrected image at the end. 
"""
