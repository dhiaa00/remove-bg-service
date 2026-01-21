
# Build:   docker build -t bg-removal-service .
# Run:     docker run -p 8000:8000 bg-removal-service
#
# Note: First request may be slow as models download on first use.
# For faster startup, you can pre-download models (see comments below).

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# - libgl1 and libglib2.0 are needed for OpenCV (used by rembg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY scripts/ ./scripts/

# Optional: Pre-download models during build
# This makes the container larger but startup faster
# Uncomment the following lines if you want pre-downloaded models:
#
# RUN python -c "from rembg import new_session; new_session('u2net')"
# RUN python -c "from withoutbg import WithoutBG; WithoutBG.opensource()"

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8000
ENV LOG_LEVEL=INFO

# Expose port (Railway will override PORT at runtime)
EXPOSE 8000

# Health check - removed because Railway doesn't use Docker healthchecks
# Railway has its own healthcheck system that hits your app's HTTP endpoint

# Run the application
CMD ["python", "-m", "app.main"]
