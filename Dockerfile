# Slim Python base — smaller image, faster deploys
FROM python:3.12-slim

WORKDIR /code

# Install deps first (separate layer) so Docker caches this step
# and doesn't reinstall everything every time you change app code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the actual app code
COPY ./app ./app

# Most deploy platforms (Render, Railway) inject a $PORT env var.
# Default to 8000 for local `docker run`.
ENV PORT=8000
EXPOSE 8000

# Shell form so $PORT actually gets substituted at container start
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
