# Use Python slim image for CPU environment
FROM python:3.10

# Add this line to avoid expired repository metadata issues
RUN apt-get -o Acquire::Check-Valid-Until=false update

# Install system dependencies (ffmpeg and flac are included based on your original Dockerfile)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    flac \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt to /app
COPY requirements.txt /app/requirements.txt

# Install Python packages from requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN pip install aiohttp

# Copy the current directory contents into the container at /app
COPY . /app

# Expose port 8000 to the outside world
EXPOSE 8000

# Define environment variable (optional)
ENV PORT=8000

# Run uvicorn server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
