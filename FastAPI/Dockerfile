# Use an official Python runtime as a parent image
FROM docker.arvancloud.ir/python:3.12-alpine

# Install ffmpeg, flac, and other necessary dependencies
RUN apk update && apk add --no-cache ffmpeg flac ffmpeg-libs && \
    apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8000 to the outside world
EXPOSE 8000

# Define environment variable (optional)
ENV PORT=8000

# Run uvicorn server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

