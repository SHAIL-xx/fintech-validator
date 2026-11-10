# Use a lightweight Python base image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install Boto3
RUN pip install --no-cache-dir boto3

# Copy the worker script into the container
COPY worker.py .

# Run the worker when the container starts
CMD ["python", "-u", "worker.py"]