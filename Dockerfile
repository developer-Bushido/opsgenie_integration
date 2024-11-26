# Use the Python base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy only requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && rm -rf /root/.cache/pip

# Copy the remaining application files into the container
COPY . .

# Set environment variables for Flask
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8080

# Expose the port for the Flask application
EXPOSE 8080

# Command to run the application
CMD ["flask", "run"]