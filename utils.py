# -*- coding: utf-8 -*-
"""
Created on Sat Feb 21 13:18:11 2026

@author: Wolfgang Reuter
"""

from PIL import Image, ImageDraw, ImageFont

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

# def add_watermark_to_image(image, watermark_text):
#     image = image.convert("RGBA")

#     watermark_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
#     draw = ImageDraw.Draw(watermark_layer)

#     # Dynamic font size based on diagonal
#     diagonal = (image.size[0]**2 + image.size[1]**2)**0.5
#     font_size = int(diagonal / 12)

#     try:
#         font = ImageFont.truetype("arial.ttf", font_size)
#     except:
#         font = ImageFont.load_default()

#     # Use textbbox instead of textsize
#     bbox = draw.textbbox((0, 0), watermark_text, font=font)
#     text_width = bbox[2] - bbox[0]
#     text_height = bbox[3] - bbox[1]

#     x = (image.size[0] - text_width) / 2
#     y = (image.size[1] - text_height) / 2

#     draw.text((x, y), watermark_text, fill=(255, 255, 255, 60), font=font)

#     watermark_layer = watermark_layer.rotate(
#         45,
#         resample=Image.BICUBIC,
#         center=(image.size[0] / 2, image.size[1] / 2)
#     )

#     combined = Image.alpha_composite(image, watermark_layer)

#     return combined


def add_watermark_to_image(image, watermark_text):
    image = image.convert("RGBA")
    
    # Try to load a TTF font, fallback to default if not found
    try:
        font_size = int((image.width**2 + image.height**2)**0.5 / 12)
        font = ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()
    
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
