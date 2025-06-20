FROM python:3.10-slim
WORKDIR /app

# Copy all files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the app (with scheduler)
CMD ["python", "app.py"]