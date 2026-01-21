#!/usr/bin/env python3
"""
Batch test script for comparing background removal models.

This script:
1. Scans a directory for images
2. Calls the API for each image with each model
3. Saves outputs in a structured format for comparison

Usage:
    python scripts/batch_test.py --input-dir ./test_images --output-dir ./output

Output structure:
    output/
    ├── image_name/
    │   ├── original.jpg
    │   ├── rembg.png
    │   └── withoutbg.png
"""
import argparse
import shutil
import sys
import time
from pathlib import Path

import requests


# Supported image extensions
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def find_images(directory: Path) -> list[Path]:
    """Find all supported images in a directory."""
    images = []
    for ext in SUPPORTED_EXTENSIONS:
        images.extend(directory.glob(f"*{ext}"))
        images.extend(directory.glob(f"*{ext.upper()}"))
    return sorted(images)


def process_image(
    image_path: Path,
    model: str,
    api_url: str
) -> tuple[bytes | None, float]:
    """
    Call the API to process an image.
    
    Returns:
        Tuple of (image_bytes or None, processing_time)
    """
    url = f"{api_url.rstrip('/')}/remove-background"
    
    start_time = time.time()
    
    try:
        with open(image_path, "rb") as f:
            files = {"image": (image_path.name, f, "image/jpeg")}
            data = {"model": model}
            
            response = requests.post(url, files=files, data=data, timeout=120)
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            return response.content, elapsed
        else:
            print(f"  ✗ Error: {response.status_code} - {response.text}")
            return None, elapsed
            
    except requests.exceptions.RequestException as e:
        elapsed = time.time() - start_time
        print(f"  ✗ Request failed: {e}")
        return None, elapsed


def main():
    parser = argparse.ArgumentParser(
        description="Batch test background removal models via API"
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Directory containing input images"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./output"),
        help="Directory for output images (default: ./output)"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--models",
        type=str,
        nargs="+",
        default=["rembg", "withoutbg"],
        help="Models to test (default: rembg withoutbg)"
    )
    
    args = parser.parse_args()
    
    # Validate input directory
    if not args.input_dir.exists():
        print(f"Error: Input directory not found: {args.input_dir}")
        sys.exit(1)
    
    # Find images
    images = find_images(args.input_dir)
    if not images:
        print(f"No images found in {args.input_dir}")
        sys.exit(1)
    
    print(f"Found {len(images)} images")
    print(f"Testing models: {', '.join(args.models)}")
    print(f"API URL: {args.api_url}")
    print("-" * 50)
    
    # Check API is running
    try:
        response = requests.get(f"{args.api_url}/", timeout=5)
        if response.status_code != 200:
            print(f"Warning: API health check returned {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error: Cannot connect to API at {args.api_url}")
        print(f"Make sure the server is running: python -m app.main")
        sys.exit(1)
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each image
    results = []
    total_start = time.time()
    
    for i, image_path in enumerate(images, 1):
        image_name = image_path.stem
        print(f"\n[{i}/{len(images)}] Processing: {image_path.name}")
        
        # Create output directory for this image
        image_output_dir = args.output_dir / image_name
        image_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy original
        original_dest = image_output_dir / f"original{image_path.suffix}"
        shutil.copy2(image_path, original_dest)
        print(f"  → Saved original")
        
        # Process with each model
        image_result = {"name": image_name, "timings": {}}
        
        for model in args.models:
            print(f"  → Processing with {model}...", end=" ", flush=True)
            
            result_bytes, elapsed = process_image(image_path, model, args.api_url)
            image_result["timings"][model] = elapsed
            
            if result_bytes:
                output_path = image_output_dir / f"{model}.png"
                with open(output_path, "wb") as f:
                    f.write(result_bytes)
                print(f"✓ ({elapsed:.2f}s)")
            else:
                print(f"✗ ({elapsed:.2f}s)")
        
        results.append(image_result)
    
    # Print summary
    total_elapsed = time.time() - total_start
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total images processed: {len(images)}")
    print(f"Total time: {total_elapsed:.2f}s")
    print(f"Output directory: {args.output_dir.absolute()}")
    
    print("\nAverage processing times:")
    for model in args.models:
        times = [r["timings"].get(model, 0) for r in results if r["timings"].get(model)]
        if times:
            avg = sum(times) / len(times)
            print(f"  {model}: {avg:.2f}s average")
    
    print("\nResults saved. Compare outputs side-by-side to evaluate quality.")


if __name__ == "__main__":
    main()
