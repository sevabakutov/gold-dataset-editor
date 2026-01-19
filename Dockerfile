FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy source code
COPY src/ src/
COPY slots_schema.yaml .

# Create data directory
RUN mkdir -p /data

# Expose port
EXPOSE 8000

# Set environment variables
ENV GOLD_EDITOR_DATA_ROOT=/data
ENV GOLD_EDITOR_HOST=0.0.0.0
ENV GOLD_EDITOR_PORT=8000

# Run the application
CMD ["python", "-m", "gold_dataset_editor", "--data-root", "/data", "--host", "0.0.0.0"]
