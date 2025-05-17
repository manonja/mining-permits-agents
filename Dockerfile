# Stage 1: Build package
FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set up working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./

# Create a virtual environment using uv
RUN uv venv /opt/venv

# Activate the virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Copy the rest of the project
COPY . .

# Install the package in development mode, which will install
# all dependencies and build dependencies (including hatchling)
RUN uv pip install -e .

# Stage 2: Run application
FROM python:3.12-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Create non-root user with specific UID/GID
RUN groupadd -g 4200 appuser && \
    useradd -u 4200 -g 4200 -s /bin/bash -m appuser

# Set up working directory
WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Fix permissions
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser:appuser

# Expose port
EXPOSE 8080

# Run uvicorn
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
