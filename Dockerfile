# === Base image ===
FROM python:3.11-slim

# === Set work directory ===
WORKDIR /app

# === Copy requirements and install ===
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# === Copy all project files ===
COPY . .

# === Expose port and run ===
EXPOSE 8000
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
