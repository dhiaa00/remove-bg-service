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
        print(f"Calling API: {API_URL}/remove-background with model={model}")
        response = requests.post(
            f"{API_URL}/remove-background",
            files={"image": ("image.png", buffer, "image/png")},
            data={"model": model},
            timeout=300  # Increased timeout for withoutbg (may need to download ~320MB)
        )
        
        if response.status_code == 200:
            result = Image.open(io.BytesIO(response.content))
            print(f"Success: {model} returned image {result.size}")
            return result
        else:
            error_msg = f"API error for {model}: {response.status_code} - {response.text}"
            print(error_msg)
            gr.Warning(error_msg)
            return None
            
    except requests.exceptions.Timeout:
        error_msg = f"Timeout error for {model}. Model may be downloading (first request takes 1-2 minutes)."
        print(error_msg)
        gr.Warning(error_msg)
        return None
    except Exception as e:
        error_msg = f"Request failed for {model}: {str(e)}"
        print(error_msg)
        gr.Warning(error_msg)
        return None


def process_image(image: Image.Image, progress=gr.Progress()):
    """Process image with both models and return results."""
    if image is None:
        return None, None, None, "Please upload an image first."
    
    status_msg = ""
    
    # Process with rembg
    progress(0.1, desc="Processing with rembg...")
    status_msg += "🔄 Processing with rembg...\n"
    rembg_result = remove_background(image, "rembg")
    
    if rembg_result:
        status_msg += "✅ rembg completed\n"
    else:
        status_msg += "❌ rembg failed\n"
    
    # Process with withoutbg
    progress(0.5, desc="Processing with withoutbg (may take 1-2 min on first request)...")
    status_msg += "🔄 Processing with withoutbg...\n"
    withoutbg_result = remove_background(image, "withoutbg")
    
    if withoutbg_result:
        status_msg += "✅ withoutbg completed\n"
    else:
        status_msg += "❌ withoutbg failed (check if model is initialized)\n"
    
    progress(1.0, desc="Done!")
    status_msg += "\n✅ Processing complete!"
    
    return image, rembg_result, withoutbg_result, status_msg


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
        
        status_box = gr.Textbox(
            label="Status",
            lines=5,
            interactive=False,
            placeholder="Status messages will appear here..."
        )
        
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
            outputs=[original_output, rembg_output, withoutbg_output, status_box]
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
