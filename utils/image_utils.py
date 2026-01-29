"""
Image utility functions for preprocessing and validation.
"""
import base64
from io import BytesIO
from PIL import Image
import re


def validate_image(file) -> bool:
    """Validate that the uploaded file is a valid JPG or PNG image."""
    try:
        img = Image.open(file)
        return img.format in ['JPEG', 'PNG', 'JPG']
    except Exception:
        return False


def resize_image_for_api(image: Image.Image, max_size: int = 1024) -> Image.Image:
    """
    Resize image to optimal size for API processing.
    Maintains aspect ratio while ensuring longest side doesn't exceed max_size.
    """
    width, height = image.size
    
    if width <= max_size and height <= max_size:
        return image
    
    if width > height:
        new_width = max_size
        new_height = int(height * (max_size / width))
    else:
        new_height = max_size
        new_width = int(width * (max_size / height))
    
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def image_to_base64(image: Image.Image, format: str = "JPEG") -> str:
    """Convert PIL Image to base64 encoded string."""
    buffered = BytesIO()
    image.save(buffered, format=format)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


def prepare_image_for_model(uploaded_file) -> tuple[Image.Image, str]:
    """
    Prepare uploaded image for model processing.
    Returns tuple of (PIL Image, base64 string).
    """
    image = Image.open(uploaded_file)
    
    # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Resize for optimal processing
    image = resize_image_for_api(image)
    
    # Get base64 encoding
    b64_string = image_to_base64(image)
    
    return image, b64_string


def get_image_dimensions(image: Image.Image) -> dict:
    """Get image dimensions and aspect ratio."""
    width, height = image.size
    return {
        'width': width,
        'height': height,
        'aspect_ratio': width / height if height > 0 else 1
    }
