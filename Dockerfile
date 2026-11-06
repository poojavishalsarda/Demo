# Red Hat UBI-based Minimal Container Image for Security Compliance
FROM registry.redhat.io/ubi9/python-311-minimal:latest

# Create non-root user and group
RUN useradd -m -u 1001 appuser

# Set working directory
WORKDIR /app

# Copy dependency specifications and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code with non-root ownership
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER 1001

# Expose internal port
EXPOSE 8000

# Run FastAPI with Uvicorn bound to localhost/127.0.0.1
CMD ["uvicorn", "src.main:app", "--host", "127.0.0.1", "--port", "8000"]
