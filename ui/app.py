#!/usr/bin/env python3
"""
Gradio UI for Background Removal Comparison

This provides a simple web interface for:
- Uploading an image
- Seeing side-by-side results from both models
- Quick visual comparison

Run with: python ui/app.py
          or: gradio ui/app.py
"""
import io
import os
from pathlib import Path

import gradio as gr
import requests
from PIL import Image


# Default API URL - can be overridden via environment variable
API_URL = os.environ.get("API_URL", "http://localhost:8000")


def remove_background(image: Image.Image, model: str) -> Image.Image | None:
    """Call the API to remove background."""
    if image is None:
        return None
    
    # Convert PIL Image to bytes
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    
    try:
        response = requests.post(
            f"{API_URL}/remove-background",
            files={"image": ("image.png", buffer, "image/png")},
            data={"model": model},
            timeout=120
        )
        
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
        else:
            print(f"API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Request failed: {e}")
        return None


def process_image(image: Image.Image):
    """Process image with both models and return results."""
    if image is None:
        return None, None, None
    
    # Process with both models
    rembg_result = remove_background(image, "rembg")
    withoutbg_result = remove_background(image, "withoutbg")
    
    return image, rembg_result, withoutbg_result


def create_app():
    """Create the Gradio interface."""
    
    with gr.Blocks(
        title="Background Removal Comparison",
        theme=gr.themes.Soft()
    ) as app:
        gr.Markdown(f"""
        # 🎨 Background Removal Model Comparison
        
        Upload an image to compare results from **rembg** and **withoutbg** models.
        
        > **Note**: API server: `{API_URL}`
        """)
        
        with gr.Row():
            input_image = gr.Image(
                label="Upload Image",
                type="pil",
                height=300
            )
        
        process_btn = gr.Button("Remove Background", variant="primary", size="lg")
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Original")
                original_output = gr.Image(label="Original", height=300)
            
            with gr.Column():
                gr.Markdown("### rembg")
                rembg_output = gr.Image(label="rembg Result", height=300)
            
            with gr.Column():
                gr.Markdown("### withoutbg")
                withoutbg_output = gr.Image(label="withoutbg Result", height=300)
        
        # Connect the button
        process_btn.click(
            fn=process_image,
            inputs=[input_image],
            outputs=[original_output, rembg_output, withoutbg_output]
        )
        
        gr.Markdown("""
        ---
        
        ### Tips for Comparison
        - Look at edges around hair/fur - this reveals model quality
        - Check for artifacts in transparent areas
        - Compare processing time (visible in server logs)
        
        ### About the Models
        - **rembg**: Uses U2Net, mature and widely used
        - **withoutbg**: Uses Focus v1.0.0, newer with good edge detection
        """)
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name=os.environ.get("GRADIO_SERVER_NAME", "0.0.0.0"),
        server_port=int(os.environ.get("GRADIO_SERVER_PORT", "7860")),
        share=False
    )
