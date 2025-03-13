# Use official Python image
FROM python:3.10

# Set the working directory inside the container
WORKDIR /app

# Copy the project files to the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the application port
EXPOSE 80

# Run workers
CMD ["uvicorn", "run:app", "--host", "0.0.0.0", "--port", "80"]