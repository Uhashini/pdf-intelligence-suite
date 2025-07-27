# Base image with Python 3.11
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install numpy first (critical for PyTorch)
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --prefer-binary --no-cache-dir numpy && \
    pip install --prefer-binary --retries 10 --timeout 100 --no-cache-dir --progress-bar off --disable-pip-version-check \
    -r requirements.txt -f https://download.pytorch.org/whl/torch_stable.html

# Copy application code
COPY . .

# Default run command
CMD ["python", "src/main.py"]
