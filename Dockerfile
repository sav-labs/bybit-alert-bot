FROM python:3.11-slim

WORKDIR /app

# Install required packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY . .

# Create directories for logs and data
RUN mkdir -p logs data

# Run the bot
CMD ["python", "main.py"] 