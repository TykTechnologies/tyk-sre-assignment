FROM python:3.10-alpine

# Set the working directory
WORKDIR /app

# Copy the current directory into the container at /app
COPY . /app

# Install python requirements & add non-root user
RUN pip install -r /app/requirements.txt \
    && adduser -D tykuser \
    && chown -R tykuser:tykuser /app \
    && apk add --no-cache bash

# Switch to the non-root user
USER tykuser

# Expose port
EXPOSE 8080

# Run the app
CMD ["python3", "main.py"]
