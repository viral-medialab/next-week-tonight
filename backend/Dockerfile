# Use Python 3.10.13 to match your runtime.txt
FROM python:3.10.13-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port your Flask app runs on
EXPOSE 5000

# Set environment variables for Flask
ENV FLASK_APP=news_broom.py
ENV FLASK_ENV=production
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Command to run your Flask application
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]