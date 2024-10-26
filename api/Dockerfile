FROM python:3.8

WORKDIR /usr/src/app

# Install dependencies
RUN pip install fastapi fastavro redis requests click confluent_kafka uvicorn

# Copy application code
COPY app.py ./

# Create volume for auth
VOLUME ["/usr/src/app/auth"]

# Expose port
EXPOSE 3003

# Using host network to access Redis on VM
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3003", "--proxy-headers"]
