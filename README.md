# Background Removal API

A production-ready FastAPI service for removing image backgrounds using open-source ML models.

## Features

- **Two background removal models**: rembg (U2Net) and withoutbg (Focus v1.0.0)
- **Clean API**: Simple POST endpoint with model selection
- **Production-ready**: Input validation, error handling, structured logging
- **Dockerized**: Easy deployment
- **Batch testing**: Script to compare models on multiple images
- **Comparison UI**: Gradio interface for visual comparison (bonus)

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Server

```bash
# Using Python directly
python -m app.main

# Or with uvicorn (more options)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

### 3. Test the API

```bash
# Health check
curl http://localhost:8000/

# Remove background with rembg
# Note: The '@' symbol is required before the file path to tell curl to upload the file
curl -X POST http://localhost:8000/remove-background \
  -F "image=@/path/to/your/image.jpg" \
  -F "model=rembg" \
  --output result_rembg.png

# Remove background with withoutbg
curl -X POST http://localhost:8000/remove-background \
  -F "image=@/path/to/your/image.jpg" \
  -F "model=withoutbg" \
  --output result_withoutbg.png
```

## API Reference

### `POST /remove-background`

Remove background from an image.

**Request:**

- Content-Type: `multipart/form-data`
- `image`: Image file (JPEG, PNG, or WebP)
- `model`: Model to use (`rembg` or `withoutbg`)

**Response:**

- Content-Type: `image/png`
- PNG image with transparent background

**Error Responses:**

- `400`: Invalid image or unsupported model
- `413`: File too large (default max: 10MB)
- `500`: Processing error

### `GET /`

Health check endpoint. Returns service status and available models.

### `GET /models`

List available background removal models.

## Docker Deployment

### Docker Compose

Run both the API service and UI together:

```bash
# Build and start both services
docker-compose up --build

# Or run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Access:

- **API**: http://localhost:8000
- **UI**: http://localhost:7860

### Option 2: API Only (Original)

Run just the API service:

```bash
# Build the image
docker build -t bg-removal-service .

# Run the container
docker run -p 8000:8000 bg-removal-service

# With environment variables
docker run -p 8000:8000 \
  -e LOG_LEVEL=DEBUG \
  -e MAX_FILE_SIZE_MB=20 \
  bg-removal-service
```

### Option 3: UI Only

Run just the UI (requires API running separately):

```bash
# Build the UI image
docker build -f Dockerfile.ui -t bg-removal-ui .

# Run the UI container (with API on localhost)
docker run -p 7860:7860 \
  -e API_URL=http://localhost:8000 \
  bg-removal-ui

# Or connect to API in another container
docker run -p 7860:7860 \
  --network host \
  -e API_URL=http://localhost:8000 \
  bg-removal-ui
```

## Batch Testing

Compare models on multiple images:

```bash
# Put test images in a directory
mkdir test_images
# ... add images ...

# Run batch test (server must be running)
python scripts/batch_test.py \
  --input-dir ./test_images \
  --output-dir ./output

# Check results
ls output/
```

Output structure:

```
output/
├── image1/
│   ├── original.jpg
│   ├── rembg.png
│   └── withoutbg.png
├── image2/
│   └── ...
```

## Comparison UI (Bonus)

Visual comparison interface using Gradio.

### Local Development

```bash
# Install UI dependencies
pip install -r requirements-ui.txt

# Run (server must be running first)
python ui/app.py
```

Open `http://localhost:7860` in your browser.

### Docker Deployment

The UI is included in the Docker Compose setup. See [Docker Deployment](#docker-deployment) section above.

If running UI separately with custom API URL:

```bash
# Set API URL
export API_URL=http://your-api-server:8000

# Run UI
python ui/app.py
```

## Configuration

### API Service

Configuration via environment variables (or `.env` file):

| Variable           | Default   | Description     |
| ------------------ | --------- | --------------- |
| `HOST`             | `0.0.0.0` | Server host     |
| `PORT`             | `8000`    | Server port     |
| `LOG_LEVEL`        | `INFO`    | Logging level   |
| `MAX_FILE_SIZE_MB` | `10`      | Max upload size |

### UI Service

| Variable             | Default                 | Description     |
| -------------------- | ----------------------- | --------------- |
| `API_URL`            | `http://localhost:8000` | Backend API URL |
| `GRADIO_SERVER_NAME` | `0.0.0.0`               | UI server host  |
| `GRADIO_SERVER_PORT` | `7860`                  | UI server port  |

## Model Comparison

| Aspect           | rembg                 | withoutbg       |
| ---------------- | --------------------- | --------------- |
| **Model**        | U2Net                 | Focus v1.0.0    |
| **Maturity**     | Established (17k+ ⭐) | Newer (~600 ⭐) |
| **Size**         | ~176MB                | ~320MB          |
| **Speed**        | Fast                  | Moderate        |
| **Edge Quality** | Good                  | Very good       |
| **Best For**     | General use, speed    | Quality edges   |

**Recommendation**: Use **rembg** as default for speed and reliability. Use **withoutbg** when edge quality is critical (e.g., hair, fur, fine details).

## Project Structure

```
├── app/
│   ├── main.py           # FastAPI entry point
│   ├── api.py            # API routes
│   ├── config.py         # Configuration
│   ├── logging_config.py # Logging setup
│   ├── models/           # Background removal models
│   │   ├── base.py       # Abstract interface
│   │   ├── rembg_model.py
│   │   └── withoutbg_model.py
│   └── services/
│       └── bg_removal.py # Model registry
├── scripts/
│   └── batch_test.py     # Batch comparison script
├── ui/
│   └── app.py            # Gradio UI (bonus)
├── Dockerfile
├── requirements.txt
└── README.md
```

## License

MIT
