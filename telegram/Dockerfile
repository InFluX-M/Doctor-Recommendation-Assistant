# Use an official Python runtime as a parent image
FROM docker.arvancloud.ir/python:3.12-alpine

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt to /app
COPY requirements.txt /app/requirements.txt

# Install any necessary dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Make port 8001 available to the world outside this container
EXPOSE 8001

# Define environment variable
ENV TOKEN=

# Run bot.py when the container launches
CMD ["python", "main.py"]
