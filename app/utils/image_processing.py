"""
Image processing utilities for disease detection.
Handles image conversion, resizing, and normalization.
"""
import base64
import io
import logging
from typing import Tuple, Optional

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Handles image processing for disease detection."""
    
    @staticmethod
    def decode_base64_image(base64_string: str) -> Image.Image:
        """
        Decode base64 image string to PIL Image.
        
        Args:
            base64_string: Base64 encoded image string (with or without 'data:image/...' prefix)
            
        Returns:
            PIL Image object
            
        Raises:
            ValueError: If decoding fails
        """
        try:
            # Remove data URI scheme if present
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            image_data = base64.b64decode(base64_string)
            img = Image.open(io.BytesIO(image_data))
            logger.info("Base64 image decoded successfully")
            return img
            
        except Exception as e:
            logger.error(f"Error decoding base64 image: {str(e)}")
            raise ValueError(f"Failed to decode image: {str(e)}")
    
    @staticmethod
    def convert_to_rgb(img: Image.Image) -> Image.Image:
        """
        Convert image to RGB format.
        Handles RGBA, grayscale, and other formats.
        
        Args:
            img: PIL Image object
            
        Returns:
            Image in RGB format
        """
        try:
            if img.mode == 'RGBA':
                # Create white background and paste image
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
                return rgb_img
            elif img.mode != 'RGB':
                # Convert other modes (L, P, etc.) to RGB
                return img.convert('RGB')
            return img
            
        except Exception as e:
            logger.error(f"Error converting image to RGB: {str(e)}")
            raise ValueError(f"Failed to convert image to RGB: {str(e)}")
    
    @staticmethod
    def preprocess_image(img: Image.Image, target_size: Tuple[int, int] = (128, 128)) -> np.ndarray:
        """
        Preprocess image for model prediction.
        Resizes, converts to array, normalizes values.
        
        Args:
            img: PIL Image object
            target_size: Target image size (width, height)
            
        Returns:
            Preprocessed image array (4D tensor ready for model)
        """
        try:
            # Resize image
            img = img.resize(target_size, Image.Resampling.LANCZOS)
            
            # Convert to float32 array (channels last, RGB)
            img_array = np.asarray(img, dtype=np.float32)
            
            # Normalize to 0-1 range
            img_array = img_array / 255.0
            
            # Add batch dimension
            img_array = np.expand_dims(img_array, axis=0)
            
            logger.info(f"Image preprocessed successfully: shape {img_array.shape}")
            return img_array
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            raise ValueError(f"Failed to preprocess image: {str(e)}")
    
    @staticmethod
    def process_image_for_prediction(
        base64_string: str,
        target_size: Tuple[int, int] = (128, 128)
    ) -> np.ndarray:
        """
        Complete pipeline: decode, convert, preprocess.
        
        Args:
            base64_string: Base64 encoded image
            target_size: Target image size
            
        Returns:
            Preprocessed image array ready for model prediction
        """
        try:
            img = ImageProcessor.decode_base64_image(base64_string)
            img = ImageProcessor.convert_to_rgb(img)
            processed = ImageProcessor.preprocess_image(img, target_size)
            return processed
            
        except Exception as e:
            logger.error(f"Error in image processing pipeline: {str(e)}")
            raise
