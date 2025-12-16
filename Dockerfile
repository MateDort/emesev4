FROM python:3.12-slim

WORKDIR /app

# Copy backend requirements and install dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy the entire backend directory
COPY backend/ /app/backend/

# Copy root main.py
COPY main.py /app/

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]

