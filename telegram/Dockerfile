# Use an official Python runtime as a parent image
FROM docker.arvancloud.ir/python:3.12-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any necessary dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8001 available to the world outside this container
EXPOSE 8001

# Define environment variable
ENV TOKEN=7398608021:AAHslR_-iBMF9rWyyYvJUZldv3yoHa9W33Y

# Run bot.py when the container launches
CMD ["python", "main.py"]
