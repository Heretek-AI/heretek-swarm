FROM python:3.12-slim

# Create non-root user for security
RUN useradd -m -u 1001 appuser

WORKDIR /app

# Install libpq for psycopg
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only necessary files — owned by root so runtime user cannot write (S6504)
COPY --chown=root:root requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy source code only (not entire project) — owned by root so runtime user cannot modify
COPY --chown=root:root src/ ./src/

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

# Create history directory for mem0
RUN mkdir -p /app/history && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
