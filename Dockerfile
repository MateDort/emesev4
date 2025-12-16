FROM python:3.12-slim

WORKDIR /app

# Copy backend requirements and install dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the entire backend directory
COPY backend/ /app/

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# Set working directory and run the application
WORKDIR /app
CMD ["python", "main.py"]

