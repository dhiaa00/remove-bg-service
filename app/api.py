"""
API routes.
"""
import io
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from PIL import Image

from app.config import get_settings
from app.services.bg_removal import get_model, list_available_models
from app.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


def validate_image_file(file: UploadFile) -> None:
    """
    Validate uploaded file is an acceptable image.
    
    Checks:
    1. File has a filename
    2. Extension is in allowed list
    3. File size is within limits
    
    Raises:
        HTTPException: 400 for invalid type, 413 for too large
    """
    settings = get_settings()
    
    # Check filename exists
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Check extension
    extension = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if extension not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: .{extension}. "
                   f"Allowed: {', '.join(settings.allowed_extensions)}"
        )


async def validate_file_size(file: UploadFile) -> bytes:
    """
    Read file content and validate size.
    
    We need to read the content to check size (content-length header
    can be spoofed or missing). This also gives us the bytes for processing.
    
    Returns:
        File content as bytes
        
    Raises:
        HTTPException: 413 if file too large
    """
    settings = get_settings()
    
    content = await file.read()
    
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
        )
    
    return content


@router.get("/")
async def health_check():
    """
    Health check endpoint.
    
    Returns basic service info and available models.
    """
    return {
        "status": "healthy",
        "service": "background-removal-api",
        "available_models": list_available_models()
    }


@router.post("/remove-background")
async def remove_background(
    image: Annotated[UploadFile, File(description="Image file to process")],
    model: Annotated[str, Form(description="Model to use: rembg or withoutbg")]
) -> StreamingResponse:
    """
    Remove background from an uploaded image.
    
    This endpoint:
    1. Validates the uploaded file (type, size)
    2. Validates the model parameter
    3. Processes the image
    4. Returns PNG with transparent background
    
    Request:
        - multipart/form-data
        - image: file (JPEG, PNG, or WebP)
        - model: string ("rembg" or "withoutbg")
    
    Response:
        - PNG image with transparent background
        - Content-Type: image/png
    
    Errors:
        - 400: Invalid image or unsupported model
        - 413: File too large
        - 500: Processing error
    """
    logger.info(f"Received request: model={model}, filename={image.filename}")
    
    # Validate file type
    validate_image_file(image)
    
    # Read and validate file size
    content = await validate_file_size(image)
    
    # Validate model
    available = list_available_models()
    if model not in available:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported model: '{model}'. Available: {', '.join(available)}"
        )
    
    try:
        # Load image from bytes
        input_image = Image.open(io.BytesIO(content))
        
        # Convert to RGB if needed (some models don't handle RGBA input well)
        if input_image.mode not in ("RGB", "RGBA"):
            input_image = input_image.convert("RGB")
        
        logger.debug(f"Input image: {input_image.size}, mode={input_image.mode}")
        
    except Exception as e:
        logger.error(f"Failed to load image: {e}")
        raise HTTPException(
            status_code=400,
            detail="Invalid image file. Could not decode image."
        )
    
    # Process image
    try:
        remover = get_model(model)
        result = remover.remove_background(input_image)
        
        logger.debug(f"Output image: {result.size}, mode={result.mode}")
        
    except Exception as e:
        logger.error(f"Background removal failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Background removal failed: {str(e)}"
        )
    
    # Convert result to PNG bytes
    output_buffer = io.BytesIO()
    result.save(output_buffer, format="PNG")
    output_buffer.seek(0)
    
    logger.info(f"Successfully processed image with {model}")
    
    # Return as streaming response
    return StreamingResponse(
        output_buffer,
        media_type="image/png",
        headers={
            "Content-Disposition": f'inline; filename="{image.filename.rsplit(".", 1)[0]}_nobg.png"'
        }
    )


@router.get("/models")
async def list_models():
    """List available background removal models."""
    return {"models": list_available_models()}
