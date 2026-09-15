FROM python:3.14-slim

WORKDIR /app

# Install dependencies first for layer caching
COPY apps/api/pyproject.toml .
RUN pip install --no-cache-dir ".[prod]"

# Copy application code
COPY apps/api/ .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
