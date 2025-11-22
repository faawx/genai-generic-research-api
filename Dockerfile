# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.9-slim

# Allow statements and log messages to be sent straight to the terminal.
ENV PYTHONUNBUFFERED True

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#user
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Set the working directory in the container.
WORKDIR /app

# Copy the requirements file into the container.
COPY requirements.txt .

# Install the dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application's source code into the container.
COPY main.py .
COPY logger_config.py .
COPY api/ ./api/
COPY deep_research/ ./deep_research/


# Use the non-privileged user to run the application.
USER appuser

# Expose the port that the application will run on.
EXPOSE 8080

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8080 || exit 1

# Run the application.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
