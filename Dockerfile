FROM docker.io/library/python:3.11
WORKDIR /backend
ENV PYTHONUNBUFFERED 1

# Copy all files (this respects .dockerignore)
COPY . .

# Install pip requirements
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

# Apply missing database migrations and serve application
EXPOSE 80
CMD ["/bin/sh", "-c", "python manage.py migrate;python manage.py runserver 0.0.0.0:80"]

# Define healthcheck
HEALTHCHECK --interval=5s --timeout=1s --retries=10 \
    CMD wget --no-verbose --tries=1 --spider localhost/healthcheck
