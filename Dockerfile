# Use the official Python FastAPI image
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy project files into the container
COPY . /app

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose port 8000 for FastAPI
EXPOSE 8000

# Command to run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
