# --- Stage 1: Base Image (Bullseye is more stable) ---
FROM python:3.11-bullseye AS base
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /usr/src/app

# --- Stage 2: Dependencies (This gets cached) ---
FROM base AS deps
COPY requirements.txt .
# Add a very long timeout to handle slow network connections
RUN pip install --no-cache-dir --timeout 600 -r requirements.txt
# --- THE FIX IS HERE ---
# Now, forcefully install google-adk. This ensures it's always present.
RUN pip install google-adk
# --- Stage 3: Development Image (This is the target) ---
FROM base AS development
WORKDIR /usr/src/app
# Copy the full Python environment with executables
COPY --from=deps /usr/local /usr/local
# Copy your application code
COPY ./app /usr/src/app/app
# Copy the seed script so we can execute it
COPY seed.py .