FROM python:3.11-bullseye

WORKDIR /usr/src/app

# Prevent python from writing .pyc files and disable buffering
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install git (for pip git+https) and build-essential (for compiling extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy only requirements to leverage Docker cache
COPY requirements.txt .

# Install all Python dependencies from the requirements file
RUN pip install --no-cache-dir -r requirements.txt


# --- ADD A VERIFICATION STEP ---
# This will fail the build LOUDLY if google-adk is not installed correctly.
RUN python -c "import google.adk; print('SUCCESS: google.adk package was found and imported.')"

# Copy the rest of your application code
COPY . .

EXPOSE 8000